"""FastAPI application: pages, JSON API and the MCP endpoint."""
from __future__ import annotations

import json
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from jsonflow.llm.base import LLMProvider
from jsonflow.mcp.base import MCPClient
from jsonflow.server import security
from jsonflow.server.db import Database
from jsonflow.server.mcp_server import AgentMCPServer, category_slug
from jsonflow.server.services import Service, ServiceError

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "jsonflow"
_LOGIN_FAILS: dict[str, list[float]] = {}
_LOGIN_LOCK = threading.Lock()
LOCK_AFTER, LOCK_SECONDS = 5, 300


def create_app(
    data_dir: str | Path = "jsonflow_data",
    client_overrides: Optional[dict[str, MCPClient]] = None,
    llm_overrides: Optional[dict[str, LLMProvider]] = None,
    seed_examples: bool = True,
    product_name: str = "jsonflow",
) -> FastAPI:
    data_dir = Path(data_dir)
    db = Database(data_dir / "jsonflow.sqlite")
    service = Service(db, data_dir, client_overrides=client_overrides, llm_overrides=llm_overrides)
    service.bootstrap(seed_examples=seed_examples)
    mcp = AgentMCPServer(service)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        service.shutdown()

    app = FastAPI(title=product_name, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.service = service
    app.state.db = db
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    # ------------------------------------------------------------ middleware
    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
            if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
                return JSONResponse({"error": "Missing request header."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if not path.startswith("/mcp"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ServiceError)
    async def service_error(_request: Request, exc: ServiceError):
        return JSONResponse({"error": str(exc)}, status_code=exc.status)

    # ------------------------------------------------------------------ auth
    def current_user(request: Request) -> dict[str, Any]:
        user = security.user_for_session(db, request.cookies.get(security.SESSION_COOKIE))
        if not user:
            raise HTTPException(status_code=401, detail="Sign in required.")
        return user

    def super_admin(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Super admin only.")
        return user

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    async def body(request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
        except (json.JSONDecodeError, ValueError):
            raise ServiceError("Request body must be JSON.")
        if not isinstance(data, dict):
            raise ServiceError("Request body must be a JSON object.")
        return data

    @app.post("/api/auth/login")
    async def login(request: Request):
        data = await body(request)
        username = str(data.get("username", "")).strip().lower()
        password = str(data.get("password", ""))
        with _LOGIN_LOCK:
            fails = [t for t in _LOGIN_FAILS.get(username, []) if time.time() - t < LOCK_SECONDS]
            _LOGIN_FAILS[username] = fails
            if len(fails) >= LOCK_AFTER:
                return JSONResponse({"error": "Too many attempts. Try again in a few minutes."}, status_code=429)
        user = db.one("SELECT * FROM users WHERE username = ?", (username,))
        if not user or not user["active"] or not security.verify_password(password, user["password_hash"]):
            with _LOGIN_LOCK:
                _LOGIN_FAILS.setdefault(username, []).append(time.time())
            return JSONResponse({"error": "Wrong username or password."}, status_code=401)
        with _LOGIN_LOCK:
            _LOGIN_FAILS.pop(username, None)
        token = security.create_session(db, user["id"])
        db.audit(username, "auth.login")
        resp = JSONResponse({"username": user["username"], "role": user["role"]})
        resp.set_cookie(security.SESSION_COOKIE, token, httponly=True, samesite="lax",
                        secure=request.url.scheme == "https", max_age=security.SESSION_HOURS * 3600, path="/")
        return resp

    @app.post("/api/auth/logout")
    async def logout(request: Request):
        security.end_session(db, request.cookies.get(security.SESSION_COOKIE))
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(security.SESSION_COOKIE, path="/")
        return resp

    @app.get("/api/me")
    def me(user=Depends(current_user)):
        return {**user, "product": product_name}

    @app.get("/api/session")
    def session(request: Request):
        """Signed-in user or null, always 200: lets public pages render their header quietly."""
        return {"user": security.user_for_session(db, request.cookies.get(security.SESSION_COOKIE))}

    @app.post("/api/me/password")
    async def change_password(request: Request, user=Depends(current_user)):
        data = await body(request)
        row = db.one("SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        if not security.verify_password(str(data.get("current", "")), row["password_hash"]):
            raise ServiceError("Current password is wrong.", 403)
        service.set_password(user["id"], str(data.get("new", "")), user["username"])
        return {"ok": True, "signed_out": True}

    # ------------------------------------------------------------ categories
    @app.get("/api/categories")
    def categories(user=Depends(current_user)):
        return service.list_categories()

    @app.post("/api/categories")
    async def add_category(request: Request, user=Depends(super_admin)):
        data = await body(request)
        service.create_category(str(data.get("name", "")), str(data.get("description", "")), user["username"])
        return {"ok": True}

    @app.delete("/api/categories/{name}")
    def delete_category(name: str, user=Depends(super_admin)):
        service.delete_category(name, user["username"])
        return {"ok": True}

    # ---------------------------------------------------------------- agents
    @app.get("/api/agents")
    def agents(user=Depends(current_user)):
        return service.list_agents()

    @app.post("/api/agents")
    async def create_agent(request: Request, user=Depends(current_user)):
        data = await body(request)
        definition = data.get("definition")
        if definition is not None and not isinstance(definition, dict):
            raise ServiceError("definition must be a JSON object.")
        agent_id = service.create_agent(str(data.get("name", "")), str(data.get("category", "")),
                                        str(data.get("description", "")), user["username"], definition)
        return {"id": agent_id}

    @app.get("/api/agents/{agent_id}")
    def get_agent(agent_id: str, user=Depends(current_user)):
        return service.get_agent(agent_id)

    @app.put("/api/agents/{agent_id}")
    async def save_agent(agent_id: str, request: Request, user=Depends(current_user)):
        data = await body(request)
        return service.save_agent(agent_id, data.get("definition"), user["username"], data.get("version"))

    @app.delete("/api/agents/{agent_id}")
    def delete_agent(agent_id: str, user=Depends(super_admin)):
        service.delete_agent(agent_id, user["username"])
        return {"ok": True}

    @app.post("/api/agents/{agent_id}/publish")
    async def publish(agent_id: str, request: Request, user=Depends(current_user)):
        data = await body(request)
        service.set_published(agent_id, bool(data.get("published")), user["username"])
        return {"ok": True}

    @app.post("/api/agents/{agent_id}/validate")
    async def validate(agent_id: str, request: Request, user=Depends(current_user)):
        data = await body(request)
        return service.validate_definition(data.get("definition") or {})

    @app.get("/api/agents/{agent_id}/versions")
    def versions(agent_id: str, user=Depends(current_user)):
        return service.list_versions(agent_id)

    @app.get("/api/agents/{agent_id}/versions/{version}")
    def version(agent_id: str, version: int, user=Depends(current_user)):
        return service.get_version(agent_id, version)

    @app.post("/api/agents/{agent_id}/run")
    async def run_agent(agent_id: str, request: Request, user=Depends(current_user)):
        data = await body(request)
        inputs = data.get("inputs") or {}
        if not isinstance(inputs, dict):
            raise ServiceError("inputs must be an object.")
        return {"run_id": service.start_run(agent_id, inputs, "ui", user["username"])}

    @app.get("/api/palette")
    def palette(refresh: int = 0, user=Depends(current_user)):
        return service.palette(refresh=bool(refresh))

    # ------------------------------------------------------------------ runs
    @app.get("/api/runs")
    def runs(agent_id: Optional[str] = None, limit: int = 50, user=Depends(current_user)):
        return service.list_runs(agent_id, limit)

    @app.get("/api/runs/{run_id}")
    def run(run_id: str, user=Depends(current_user)):
        return service.get_run(run_id)

    @app.get("/api/runs/{run_id}/{kind}/{name}")
    def run_file(run_id: str, kind: str, name: str, user=Depends(current_user)):
        return service.run_file(run_id, kind, name)

    # ----------------------------------------------------------- super admin
    @app.get("/api/users")
    def users(user=Depends(super_admin)):
        return service.list_users()

    @app.post("/api/users")
    async def add_user(request: Request, user=Depends(super_admin)):
        data = await body(request)
        uid = service.create_user(str(data.get("username", "")), str(data.get("password", "")),
                                  str(data.get("role", "admin")), str(data.get("display_name", "")), user["username"])
        return {"id": uid}

    @app.patch("/api/users/{user_id}")
    async def edit_user(user_id: int, request: Request, user=Depends(super_admin)):
        service.update_user(user_id, await body(request), user)
        return {"ok": True}

    @app.post("/api/users/{user_id}/password")
    async def reset_password(user_id: int, request: Request, user=Depends(super_admin)):
        data = await body(request)
        service.set_password(user_id, str(data.get("password", "")), user["username"])
        return {"ok": True}

    @app.get("/api/settings/servers")
    def get_servers(user=Depends(super_admin)):
        return service.servers_config()

    @app.put("/api/settings/servers")
    async def put_servers(request: Request, user=Depends(super_admin)):
        service.save_servers(await body(request), user["username"])
        return {"ok": True}

    @app.post("/api/settings/servers/{name}/test")
    def test_server(name: str, user=Depends(super_admin)):
        return service.test_server(name)

    @app.get("/api/settings/llm")
    def get_llm(user=Depends(super_admin)):
        return service.llm_status()

    @app.put("/api/settings/llm")
    async def put_llm(request: Request, user=Depends(super_admin)):
        service.save_llm(await body(request), user["username"])
        return {"ok": True}

    @app.post("/api/settings/llm/test")
    def test_llm(user=Depends(super_admin)):
        return service.test_llm()

    @app.get("/api/keys")
    def keys(user=Depends(super_admin)):
        return service.list_keys()

    @app.post("/api/keys")
    async def add_key(request: Request, user=Depends(super_admin)):
        data = await body(request)
        cats = data.get("categories") or []
        if not isinstance(cats, list):
            raise ServiceError("categories must be a list.")
        return service.create_key(str(data.get("name", "")), [str(c) for c in cats], user["username"])

    @app.delete("/api/keys/{key_id}")
    def revoke_key(key_id: int, user=Depends(super_admin)):
        service.revoke_key(key_id, user["username"])
        return {"ok": True}

    @app.get("/api/audit")
    def audit(limit: int = 200, user=Depends(super_admin)):
        return service.audit_log(limit)

    @app.get("/api/mcp/info")
    def mcp_info(request: Request, user=Depends(current_user)):
        base = str(request.base_url).rstrip("/")
        cats = [{"name": c["name"], "url": f"{base}/mcp/category/{category_slug(c['name'])}"} for c in service.list_categories()]
        return {"url": f"{base}/mcp", "categories": cats, "published": len(service.published_agents())}

    # ------------------------------------------------------------------- MCP
    async def mcp_endpoint(request: Request, category: Optional[str]):
        auth = request.headers.get("authorization", "")
        secret = auth[7:].strip() if auth.lower().startswith("bearer ") else request.headers.get("x-api-key")
        key = security.key_for_secret(db, secret)
        if not key:
            return JSONResponse({"error": "A valid API key is required."}, status_code=401,
                                headers={"WWW-Authenticate": "Bearer"})
        try:
            message = await request.json()
        except (json.JSONDecodeError, ValueError):
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, status_code=400)
        import anyio

        reply, headers = await anyio.to_thread.run_sync(mcp.handle, message, key, category)
        if reply is None:
            return Response(status_code=202)
        return JSONResponse(reply, headers=headers)

    @app.post("/mcp")
    async def mcp_all(request: Request):
        return await mcp_endpoint(request, None)

    @app.post("/mcp/category/{slug}")
    async def mcp_category(slug: str, request: Request):
        return await mcp_endpoint(request, slug)

    @app.get("/mcp")
    @app.get("/mcp/category/{slug}")
    def mcp_get(slug: str = ""):
        return Response(status_code=405, headers={"Allow": "POST"})

    @app.delete("/mcp")
    def mcp_delete():
        return Response(status_code=204)

    # ----------------------------------------------------------------- pages
    def page(name: str):
        return FileResponse(PAGES / name, headers={"Cache-Control": "no-cache"})

    @app.get("/favicon.ico")
    def favicon():
        return FileResponse(HERE / "static" / "favicon.svg", media_type="image/svg+xml")

    @app.get("/")
    def home():
        return page("home.html")

    @app.get("/guide")
    def guide():
        return page("guide.html")

    @app.get("/login")
    def login_page():
        return page("login.html")

    @app.get("/app")
    def dashboard():
        return page("dashboard.html")

    @app.get("/app/agents/{agent_id}")
    def builder(agent_id: str):
        return page("builder.html")

    @app.get("/app/runs/{run_id}")
    def run_page(run_id: str):
        return page("run.html")

    @app.get("/app/admin")
    def admin_page():
        return page("admin.html")

    return app

"""Browser walkthrough of the jsonflow product. Not collected by pytest; run by hand.

Start a fresh demo server with two users, then run:

    JSONFLOW_NEW_PASSWORD='Super-secret-1' python -m jsonflow.server create-user --username root --role super_admin --data-dir /tmp/jf
    JSONFLOW_NEW_PASSWORD='Admin-secret-1' python -m jsonflow.server create-user --username ana --role admin --data-dir /tmp/jf
    python -m jsonflow.server serve --demo --port 8765 --data-dir /tmp/jf &
    python tests/jsonflow_browser_e2e.py /tmp/jf-shots [chromium-path]

Fails on any browser console error. Screenshots go to the given folder.
"""
import sys, time, json
from playwright.sync_api import sync_playwright, expect

BASE = "http://127.0.0.1:8765"
SHOTS = sys.argv[1]
import os
os.makedirs(SHOTS, exist_ok=True)
errors = []

def watch(page):
    page.on("console", lambda m: errors.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

def login(page, user, pw):
    page.goto(BASE + "/login")
    page.fill("input[name=username]", user)
    page.fill("input[name=password]", pw)
    page.click("button[type=submit]")
    page.wait_for_url("**/app")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=sys.argv[2]) if len(sys.argv) > 2 else p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page(); watch(page)

    # public pages
    page.goto(BASE + "/"); expect(page.locator("h1")).to_contain_text("Build agents")
    page.screenshot(path=f"{SHOTS}/01_home.png", full_page=True)
    page.goto(BASE + "/guide"); expect(page.locator("#publish")).to_be_visible()
    page.screenshot(path=f"{SHOTS}/02_guide.png")
    page.goto(BASE + "/app"); page.wait_for_url("**/login?next=*")

    # admin user: dashboard
    login(page, "ana", "Admin-secret-1")
    expect(page.locator(".agent-card")).to_have_count(1)
    expect(page.locator("text=Admin").first).to_be_visible()
    assert page.locator(".nav a", has_text="Admin").count() == 0, "admin must not see Admin nav"
    page.screenshot(path=f"{SHOTS}/03_dashboard.png")

    # builder on the seeded agent
    page.click("text=Open builder")
    page.wait_for_selector(".node")
    expect(page.locator(".node")).to_have_count(12)
    page.screenshot(path=f"{SHOTS}/04_builder.png")
    page.click(".node[data-id=validate_events]")
    expect(page.locator("#insp-body")).to_contain_text("tavily_domain_search")
    expect(page.locator("#insp-body .seg").first).to_be_visible()
    page.screenshot(path=f"{SHOTS}/05_inspector_tool.png")
    page.click(".node[data-id=extract_events]")
    expect(page.locator("#insp-body")).to_contain_text("Structured output")
    page.click(".node[data-id=check_articles]")
    expect(page.locator("#insp-body")).to_contain_text("Routes, first match wins")
    page.click(".node[data-id=collect_articles]")
    expect(page.locator("#insp-body .step")).to_have_count(8)
    page.screenshot(path=f"{SHOTS}/06_inspector_transform.png")
    page.click("#btn-validate"); page.wait_for_selector(".toast")

    # run it
    page.click("#btn-run"); page.wait_for_selector(".modal")
    page.click(".modal .btn.primary")
    page.wait_for_url("**/app/runs/*")
    expect(page.locator("#run-status")).to_contain_text("succeeded", timeout=20000)
    page.wait_for_timeout(300)
    expect(page.locator(".node.st-skipped")).to_have_count(1)
    page.screenshot(path=f"{SHOTS}/07_run.png")
    page.click(".node[data-id=extract_events]")
    expect(page.locator("#insp-body")).to_contain_text("extract_events.llm1.json")
    page.click("summary:has-text('extract_events.llm1.json')")
    expect(page.locator("#insp-body pre").nth(1)).to_contain_text("prompt")
    page.screenshot(path=f"{SHOTS}/08_run_step.png")

    # new agent by drag and drop
    page.goto(BASE + "/app"); page.click("#new")
    page.fill(".modal input >> nth=0", "Reg watch")
    page.select_option(".modal select >> nth=0", "Regulatory")
    page.fill(".modal input >> nth=1", "Finds hedge fund regulation news")
    page.click(".modal .btn.primary")
    page.wait_for_url("**/app/agents/reg_watch")
    page.wait_for_selector(".node[data-id=start]")
    page.fill("#pal-search", "news")
    src = page.locator(".pal-item:has(.nm:text-is('tavily_news_search'))")
    src.drag_to(page.locator("#canvas"), target_position={"x": 520, "y": 300})
    page.wait_for_selector(".node[data-id=tavily_news_search]")
    # connect start -> news search
    port = page.locator(".node[data-id=start] .port.out").bounding_box()
    tgt = page.locator(".node[data-id=tavily_news_search]").bounding_box()
    page.mouse.move(port["x"] + 7, port["y"] + 7); page.mouse.down()
    page.mouse.move(tgt["x"] + 60, tgt["y"] + 30, steps=8); page.mouse.up()
    expect(page.locator("#insp-head")).to_contain_text("Connection")
    # configure query as a fixed value
    page.click(".node[data-id=tavily_news_search]")
    q = page.locator("#insp-body .arg", has=page.locator("label.arg-name", has_text="query")).first
    q.locator("input.input").fill("USA hedge funds regulation latest")
    # max_results: pick-from-data mode would need an input; use expression mode instead
    m = page.locator("#insp-body .arg", has=page.locator("label.arg-name", has_text="max_results")).first
    m.locator("button", has_text="Expression").click()
    m.locator("input.expr").fill("{{ 3 }}")
    # agent output = the news node
    page.mouse.click(900, 700)  # empty canvas -> agent settings
    expect(page.locator("#insp-head")).to_contain_text("Agent settings")
    out = page.locator("#insp-body section", has=page.locator("h3", has_text="Output"))
    out.locator("select").first.select_option("node")
    out.locator("select").nth(1).select_option("tavily_news_search")
    page.keyboard.press("Control+s")
    page.wait_for_selector(".toast:has-text('Saved version')")
    page.screenshot(path=f"{SHOTS}/09_new_agent.png")
    page.click("#btn-publish")
    page.wait_for_selector(".toast:has-text('Published')")
    page.click("#btn-run"); page.wait_for_selector(".modal")
    page.click(".modal .btn.primary")
    page.wait_for_url("**/app/runs/*")
    expect(page.locator("#run-status")).to_contain_text("succeeded", timeout=20000)
    expect(page.locator("#insp-body")).to_contain_text("SEC adopts amendments")
    page.screenshot(path=f"{SHOTS}/10_new_agent_run.png")

    # super admin
    ctx2 = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx2.new_page(); watch(pg)
    login(pg, "root", "Super-secret-1")
    pg.click(".nav a:has-text('Admin')")
    for tab in ["users", "categories", "servers", "llm", "keys", "audit"]:
        pg.click(f"[data-tab={tab}]")
        pg.wait_for_timeout(250)
        assert "notice bad" not in pg.inner_html("#panel"), tab
    pg.click("[data-tab=keys]")
    pg.fill("#panel input >> nth=0", "sajha-agent")
    pg.click("#panel button:has-text('Create key')")
    expect(pg.locator(".modal pre")).to_contain_text("jfk_")
    key = pg.locator(".modal pre").inner_text()
    pg.screenshot(path=f"{SHOTS}/11_admin_keys.png")
    pg.keyboard.press("Escape")
    pg.click("[data-tab=servers]"); pg.click("button:has-text('Test sajha')")
    expect(pg.locator("#panel .notice.ok")).to_contain_text("tools found")
    pg.click("[data-tab=audit]"); expect(pg.locator("#panel")).to_contain_text("agent.publish")
    pg.screenshot(path=f"{SHOTS}/12_admin_audit.png")
    b.close()
    print(json.dumps({"key": key}))

print("CONSOLE ERRORS:", errors if errors else "none")
sys.exit(1 if errors else 0)

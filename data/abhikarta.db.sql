-- ============================================
-- Database Schema Export
-- ============================================
-- Source: /home/ashutosh/PycharmProjects/abhikarta/data/abhikarta.db
-- Generated: 2025-10-30 23:00:15
-- ============================================



-- ============================================
-- Table: agent_executions
-- ============================================

DROP TABLE IF EXISTS agent_executions;
CREATE TABLE agent_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                workflow_id TEXT,
                node_id TEXT,
                input TEXT,
                output TEXT,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                error TEXT
            );

-- Columns: id, execution_id, agent_id, workflow_id, node_id, input, output, status, started_at, completed_at, error

-- ============================================
-- Table: agents
-- ============================================

DROP TABLE IF EXISTS agents;
CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                config TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

-- Columns: agent_id, name, type, config, status, created_at

-- ============================================
-- Table: hitl_requests
-- ============================================

DROP TABLE IF EXISTS hitl_requests;
CREATE TABLE hitl_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                workflow_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                responded_at TEXT,
                responded_by TEXT,
                response TEXT
            );

-- Columns: id, request_id, workflow_id, node_id, message, status, created_at, responded_at, responded_by, response

-- ============================================
-- Table: lgraph_hitl_requests
-- ============================================

DROP TABLE IF EXISTS lgraph_hitl_requests;
CREATE TABLE lgraph_hitl_requests (
            hitl_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            checkpoint TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            responded_at TEXT,
            responded_by TEXT,
            response TEXT,
            FOREIGN KEY (workflow_id) REFERENCES lgraph_workflows(workflow_id)
        );

-- Columns: hitl_id, workflow_id, plan_id, checkpoint, message, status, created_at, responded_at, responded_by, response

-- ============================================
-- Table: lgraph_plans
-- ============================================

DROP TABLE IF EXISTS lgraph_plans;
CREATE TABLE lgraph_plans (
            plan_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            user_request TEXT,
            plan_type TEXT,
            execution_plan TEXT,
            plan_summary TEXT,
            status TEXT DEFAULT 'pending_approval',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT,
            approved_by TEXT,
            rejected_at TEXT,
            rejected_by TEXT,
            rejection_reason TEXT
        );

-- Columns: plan_id, user_id, session_id, user_request, plan_type, execution_plan, plan_summary, status, created_at, approved_at, approved_by, rejected_at, rejected_by, rejection_reason

-- ============================================
-- Table: lgraph_step_logs
-- ============================================

DROP TABLE IF EXISTS lgraph_step_logs;
CREATE TABLE lgraph_step_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            step_id TEXT NOT NULL,
            result TEXT,
            success BOOLEAN,
            executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES lgraph_workflows(workflow_id)
        );

-- Columns: log_id, workflow_id, step_id, result, success, executed_at

-- ============================================
-- Table: lgraph_workflows
-- ============================================

DROP TABLE IF EXISTS lgraph_workflows;
CREATE TABLE lgraph_workflows (
            workflow_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            results TEXT,
            error TEXT,
            FOREIGN KEY (plan_id) REFERENCES lgraph_plans(plan_id)
        );

-- Columns: workflow_id, plan_id, user_id, session_id, status, started_at, completed_at, results, error

-- ============================================
-- Table: planner_conversations
-- ============================================

DROP TABLE IF EXISTS planner_conversations;
CREATE TABLE planner_conversations (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            message TEXT,
            response TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

-- Columns: conversation_id, user_id, message, response, created_at

-- ============================================
-- Table: plans
-- ============================================

DROP TABLE IF EXISTS plans;
CREATE TABLE plans (
            plan_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            request TEXT,
            plan_json TEXT,
            status TEXT DEFAULT 'pending_approval',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT,
            rejected_at TEXT,
            rejection_reason TEXT
        );

-- Columns: plan_id, user_id, request, plan_json, status, created_at, approved_at, rejected_at, rejection_reason

-- ============================================
-- Table: sessions
-- ============================================

DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                workflow_id TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                metadata TEXT
            );

-- Columns: session_id, user_id, workflow_id, status, created_at, updated_at, completed_at, metadata

-- ============================================
-- Table: tools
-- ============================================

DROP TABLE IF EXISTS tools;
CREATE TABLE tools (
                tool_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT,
                config TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

-- Columns: tool_id, name, description, type, config, status, created_at

-- ============================================
-- Table: users
-- ============================================

DROP TABLE IF EXISTS users;
CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            );

-- Columns: user_id, username, full_name, email, role, created_at, last_login

-- ============================================
-- Table: workflow_dags
-- ============================================

DROP TABLE IF EXISTS workflow_dags;
CREATE TABLE workflow_dags (
                dag_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                dag_json TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

-- Columns: dag_id, name, description, dag_json, status, created_at, updated_at

-- ============================================
-- Table: workflow_events
-- ============================================

DROP TABLE IF EXISTS workflow_events;
CREATE TABLE workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

-- Columns: id, workflow_id, event_type, event_data, created_at

-- ============================================
-- Table: workflow_executions
-- ============================================

DROP TABLE IF EXISTS workflow_executions;
CREATE TABLE workflow_executions (
                execution_id TEXT PRIMARY KEY,
                dag_id TEXT NOT NULL,
                user_id TEXT,
                status TEXT DEFAULT 'running',
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                results TEXT,
                error TEXT
            );

-- Columns: execution_id, dag_id, user_id, status, start_time, end_time, results, error

-- ============================================
-- Table: workflow_nodes
-- ============================================

DROP TABLE IF EXISTS workflow_nodes;
CREATE TABLE workflow_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                node_type TEXT,
                agent_id TEXT,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                config TEXT,
                UNIQUE(workflow_id, node_id)
            );

-- Columns: id, workflow_id, node_id, node_type, agent_id, status, started_at, completed_at, result, error, config

-- ============================================
-- Table: workflows
-- ============================================

DROP TABLE IF EXISTS workflows;
CREATE TABLE workflows (
                workflow_id TEXT PRIMARY KEY,
                dag_id TEXT NOT NULL,
                session_id TEXT,
                name TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT,
                created_by TEXT,
                graph_json TEXT,
                result TEXT,
                error TEXT
            );

-- Columns: workflow_id, dag_id, session_id, name, description, status, created_at, started_at, completed_at, created_by, graph_json, result, error

-- ============================================
-- End of schema export
-- Total: 17 tables, 0 views
-- ============================================

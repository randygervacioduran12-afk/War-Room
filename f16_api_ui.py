from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
def ui_index() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>War Room // Universal Adapter</title>
  <link rel="stylesheet" href="/f61_ui_styles.css?v=3" />
</head>
<body>
  <div class="app-shell">
    <div class="bg-orb orb-a"></div>
    <div class="bg-orb orb-b"></div>
    <div class="bg-grid"></div>

    <aside class="sidebar glass">
      <div class="brand-block">
        <div class="brand-mark">WR</div>
        <div>
          <div class="brand-title">War Room // Universal Adapter</div>
          <div class="brand-sub">connected multi-agent control</div>
        </div>
      </div>

      <div class="sidebar-status">
        <div id="mini-health"></div>
      </div>

      <nav class="sidebar-nav">
        <button class="nav-btn active" data-view="overview">Overview</button>
        <button class="nav-btn" data-view="signals">Signals</button>
        <button class="nav-btn" data-view="operations">Operations</button>
        <button class="nav-btn" data-view="notes">Notes</button>
        <button class="nav-btn" data-view="workbench">Workbench</button>
        <button class="nav-btn" data-view="projects">Projects</button>
      </nav>

      <div class="sidebar-footer">
        <button id="refresh-all-btn" class="ghost-btn">Refresh all</button>
        <button id="theme-cycle-btn" class="ghost-btn">Cycle theme</button>
        <button id="auto-poll-tasks-btn" class="ghost-btn">Auto poll: on</button>
      </div>
    </aside>

    <main class="main-stage">
      <section class="hero glass">
        <div class="hero-copy">
          <div class="eyebrow">war room link active</div>
          <h1>Universal Adapter Operations Deck</h1>
          <p>
            Spin up runs, dispatch specialist generals, summarize notes, monitor task flow,
            inspect artifacts, and operate a proper multi-agent room.
          </p>

          <div class="hero-actions">
            <button id="hero-launch-btn" class="primary-btn">Launch a run</button>
            <button id="hero-dispatch-btn" class="secondary-btn">Dispatch task</button>
          </div>

          <div class="hero-metrics">
            <div class="metric-chip">
              <span class="dot ok"></span>
              <span id="health-overview">System nominal</span>
            </div>
            <div class="metric-chip">
              <span id="active-run-id">No active run</span>
            </div>
            <div class="metric-chip wide">
              <span id="active-run-meta">Create or select a run</span>
            </div>
            <div class="metric-chip wide">
              <span id="health-meta">db=? · llm=?</span>
            </div>
            <div class="metric-chip wide">
              <span id="task-pulse">0 queued · 0 claimed</span>
            </div>
            <div class="metric-chip wide">
              <span id="task-pulse-meta">0 completed · 0 failed</span>
            </div>
            <div class="metric-chip wide">
              <span id="artifact-pulse">No artifacts</span>
            </div>
            <div class="metric-chip wide">
              <span id="artifact-pulse-meta">Dock idle</span>
            </div>
          </div>
        </div>

        <div class="hero-scene">
          <div class="scene-ring ring-1"></div>
          <div class="scene-ring ring-2"></div>
          <div class="scene-planet"></div>
          <div class="scene-pet pet-a">🦊</div>
          <div class="scene-pet pet-b">🦉</div>
          <div class="scene-pet pet-c">🐺</div>
          <div class="scene-label glass">live adaptive command surface</div>
        </div>
      </section>

      <section id="view-overview" class="view-panel active-view">
        <div class="panel-grid panel-grid-overview">
          <section class="panel glass">
            <div class="panel-head">
              <h2>System link</h2>
              <button id="health-refresh-btn" class="ghost-btn sm">Refresh</button>
            </div>
            <div id="health-cards" class="card-grid two"></div>
          </section>

          <section class="panel glass">
            <div class="panel-head">
              <h2>Signal corridor</h2>
            </div>
            <div id="signal-corridor" class="card-grid two"></div>
          </section>

          <section class="panel glass">
            <div class="panel-head">
              <h2>Pet dock</h2>
            </div>
            <div id="pet-list" class="pet-grid"></div>
          </section>

          <section class="panel glass">
            <div class="panel-head">
              <h2>Artifact dock</h2>
              <button id="load-artifacts-btn" class="ghost-btn sm">Refresh dock</button>
            </div>
            <div id="artifact-grid" class="artifact-grid"></div>
          </section>
        </div>
      </section>

      <section id="view-signals" class="view-panel">
        <div class="panel-grid panel-grid-signals">
          <section class="panel glass">
            <div class="panel-head">
              <h2>Run registry</h2>
              <button id="load-runs-btn" class="ghost-btn sm">Load runs</button>
            </div>
            <div id="runs-list" class="stack-list"></div>
          </section>

          <section class="panel glass">
            <div class="panel-head">
              <h2>Task board</h2>
              <button id="load-tasks-btn" class="ghost-btn sm">Load tasks</button>
            </div>
            <div id="task-board" class="task-lanes"></div>
          </section>
        </div>
      </section>

      <section id="view-operations" class="view-panel">
        <div class="panel-grid panel-grid-ops">
          <section class="panel glass">
            <div class="panel-head">
              <h2>Launch run</h2>
              <button id="open-launch-btn" class="ghost-btn sm">Focus</button>
            </div>

            <div class="form-grid">
              <label class="field">
                <span>Project key</span>
                <input id="run-project-key" value="demo-project" />
              </label>

              <label class="field">
                <span>Adapter key</span>
                <input id="run-adapter-key" value="research_project" />
              </label>

              <label class="field field-wide">
                <span>Goal</span>
                <textarea id="run-goal">Design an overnight AI research pipeline</textarea>
              </label>
            </div>

            <button id="create-run-btn" class="primary-btn">Launch run</button>
            <pre id="launch-result" class="result-box"></pre>
          </section>

          <section class="panel glass">
            <div class="panel-head">
              <h2>Dispatch mission</h2>
            </div>

            <div class="form-grid">
              <label class="field">
                <span>General key</span>
                <input id="dispatch-general-key" value="general_of_the_army" />
              </label>

              <label class="field">
                <span>Task type</span>
                <input id="dispatch-task-type" value="plan" />
              </label>

              <label class="field">
                <span>Title</span>
                <input id="dispatch-title" value="Manual mission dispatch" />
              </label>

              <label class="field field-wide">
                <span>Operator message</span>
                <textarea id="dispatch-message">Summarize current state and recommend the next move.</textarea>
              </label>
            </div>

            <button id="dispatch-task-btn" class="primary-btn">Dispatch mission</button>
            <pre id="dispatch-result" class="result-box"></pre>
          </section>
        </div>
      </section>

      <section id="view-notes" class="view-panel">
        <div class="panel-grid">
          <section class="panel glass">
            <div class="panel-head">
              <h2>Memory feed</h2>
              <button id="load-memory-btn" class="ghost-btn sm">Load memory</button>
            </div>
            <div id="memory-list" class="stack-list"></div>
          </section>
        </div>
      </section>

      <section id="view-workbench" class="view-panel">
        <div class="panel-grid">
          <section class="panel glass">
            <div class="panel-head">
              <h2>Workbench</h2>
              <button id="load-workbench-btn" class="ghost-btn sm">Refresh workbench</button>
            </div>

            <div class="toolbar-row">
              <label class="field compact">
                <span>Prefix filter</span>
                <input id="workbench-prefix" value="" placeholder="f6" />
              </label>
            </div>

            <div id="workbench-grid" class="file-grid"></div>
          </section>
        </div>
      </section>

      <section id="view-projects" class="view-panel">
        <div class="panel-grid">
          <section class="panel glass">
            <div class="panel-head">
              <h2>Project bridge</h2>
            </div>
            <div class="bridge-copy">
              This surface is now pinned to the FastAPI war room shell. Old frontend previews should redirect here.
            </div>
          </section>
        </div>
      </section>
    </main>
  </div>

  <div id="artifact-modal" class="modal hidden">
    <div class="modal-backdrop"></div>
    <div class="modal-card glass">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Artifact dock</div>
          <h3 id="artifact-modal-subtitle">artifact</h3>
        </div>
        <button id="close-artifact-modal" class="ghost-btn sm">Close</button>
      </div>
      <div id="artifact-modal-body" class="modal-body"></div>
    </div>
  </div>

  <script type="module" src="/f62_ui_app.js?v=3"></script>
</body>
</html>
"""
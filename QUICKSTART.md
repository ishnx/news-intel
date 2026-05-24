# Quickstart — Go Live in 4 Steps

Zero coding. ~10 minutes. You need: a GitHub account and an Anthropic API key.

---

## Step 1 — Fork the Repository

1. Go to this repository on GitHub
2. Click **Fork** (top right)
3. Give it any name you like (e.g. `world-intel`)
4. Click **Create Fork**

You now have your own copy at `github.com/YOUR-USERNAME/world-intel`

---

## Step 2 — Add Your Anthropic API Key

1. In your forked repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: your key (starts with `sk-ant-...`)
5. Click **Add secret**

Get a key at platform.anthropic.com if you don't have one yet.

---

## Step 3 — Enable GitHub Pages

1. In your repo, go to **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. Click **Save**

---

## Step 4 — Run It

1. Go to the **Actions** tab in your repo
2. Click **Intelligence Pipeline** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Wait ~5-10 minutes

That's it. Your intelligence system is live.

**Your site:** `https://YOUR-USERNAME.github.io/world-intel`

---

## What Happens Next

- The pipeline runs automatically twice a day (6am and 6pm UTC)
- Each run: fetches news → ranks stories → analyzes with Claude → generates HTML reports → commits everything back → deploys to GitHub Pages
- After ~10 runs the system starts referencing its own memory in analysis

---

## Add the Chatbot (Optional, Highly Recommended)

Each report has a built-in AI chatbot. To use it:

1. Open any report on your GitHub Pages site
2. Click **💬 Ask Claude** (bottom right)
3. Enter your Anthropic API key when prompted (stays in your browser only)
4. Start chatting

To enable memory auto-commit (so chatbot insights feed back into the pipeline):

1. Create a GitHub Personal Access Token at github.com/settings/tokens
   - Needs: `repo` scope
2. In any report chatbot, click the **⚙** gear icon
3. Enter your PAT, repo name (`YOUR-USERNAME/world-intel`), and branch (`main`)
4. Click **Connect GitHub**

Now when you chat, insights are automatically committed to your `memory/` folder and used in the next pipeline run.

---

## Customize Your Intelligence Feed

Edit `config/feeds.yaml` to add or remove news sources.
Edit `config/schedules.yaml` to change how many stories to analyze per run.
Edit `config/analysis_prompt.md` to change the analyst persona or focus.

All changes take effect on the next pipeline run.

---

## Costs

| Usage | Estimated monthly cost |
|-------|----------------------|
| 5 stories/day (default) | ~$5-10/month |
| 10 stories/day | ~$15-25/month |
| Chatbot conversations | ~$0.01-0.10 per conversation |

Costs come from Anthropic API usage only. GitHub is free.

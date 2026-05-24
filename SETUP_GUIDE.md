# Setup Guide
## Zero-to-Running in Under 10 Minutes

This guide assumes **zero coding knowledge**. Follow each step exactly.

---

## What You'll Need

- A GitHub account (free) — [github.com](https://github.com)
- An Anthropic API key — [console.anthropic.com](https://console.anthropic.com)
- About 10 minutes

---

## Step 1: Get Your Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Click **"API Keys"** in the left menu
4. Click **"Create Key"**
5. Give it a name (e.g., "Intelligence System")
6. **Copy the key** — it starts with `sk-ant-...`
7. Save it somewhere safe — you'll need it in Step 4

⚠️ **Important:** This key costs money when used (cents per analysis, not dollars).
Set up billing limits in the Anthropic console to control spending.

---

## Step 2: Create Your GitHub Repository

### Option A: Fork This Repository (Recommended)
If someone shared this repository with you:
1. Go to the repository page on GitHub
2. Click the **"Fork"** button (top right)
3. Choose your account as the destination
4. Click **"Create Fork"**

### Option B: Create a New Repository
1. Go to [github.com/new](https://github.com/new)
2. Name your repository (e.g., `world-intelligence`)
3. Set it to **Public** (required for free GitHub Pages)
4. Click **"Create Repository"**
5. Upload all files from this system to the repository

---

## Step 3: Enable GitHub Pages

This makes your reports publicly accessible on the web.

1. In your repository, click **"Settings"** (top menu)
2. In the left sidebar, scroll to **"Pages"**
3. Under "Build and deployment", set:
   - **Source:** GitHub Actions
4. Click **Save**

Your site will be at: `https://[your-username].github.io/[repo-name]/`

---

## Step 4: Add Your Anthropic API Key (Secret)

⚠️ **Critical:** Never put your API key in the code or commit it to GitHub!

1. In your repository, click **"Settings"**
2. In the left sidebar, click **"Secrets and Variables"**
3. Click **"Actions"**
4. Click **"New repository secret"**
5. Name: `ANTHROPIC_API_KEY`
6. Value: Paste your API key (starts with `sk-ant-...`)
7. Click **"Add secret"**

You should now see `ANTHROPIC_API_KEY` in your secrets list.

---

## Step 5: Test the Pipeline (First Run)

Let's make sure everything works before trusting the automation.

1. In your repository, click the **"Actions"** tab
2. In the left sidebar, click **"Intelligence Pipeline"**
3. Click **"Run workflow"** (right side, blue button)
4. Leave settings as default
5. Click **"Run workflow"** to confirm

The pipeline will take 5-15 minutes to complete. Watch for:
- Green checkmark ✓ = Success
- Red X = Error (see troubleshooting below)

---

## Step 6: View Your First Reports

After the pipeline completes:

1. Go to: `https://[your-username].github.io/[repo-name]/`
2. You should see the intelligence dashboard with your first reports
3. Click any report card to view the full analysis
4. Try the chatbot in the bottom-right corner (you'll enter your API key there)

---

## Step 7: Configure the Chatbot (in Reports)

Each HTML report has an embedded chatbot. To use it:

1. Open any intelligence report
2. Click **"💬 Ask Claude"** (bottom right)
3. You'll see a field to enter your Anthropic API key
4. Enter your API key (starts with `sk-ant-...`)
5. Click **"Save"**
6. The key is stored only in your browser — never uploaded to GitHub

Now you can ask the chatbot anything about the report.

---

## Step 8: Customize Your Intelligence Feeds

The system comes with default news feeds. Customize them:

1. In your repository, navigate to `config/feeds.yaml`
2. Click the **pencil icon** to edit
3. Add your preferred news sources:
   ```yaml
   - name: "Your Favorite Source"
     url: "https://example.com/rss"
     trust: 0.85
   ```
4. Click **"Commit changes"**

To find an RSS feed URL for any website:
- Look for the RSS icon (orange symbol) on the website
- Or try adding `/feed`, `/rss`, or `/feed.xml` to the domain
- Or search: "[website name] RSS feed URL"

---

## Step 9: Customize Your Worldview

Tell the system what you care about:

1. In your repository, navigate to `config/worldview.md`
2. Click the **pencil icon** to edit
3. Add your own analytical priors and beliefs
4. Change the topic weights in `config/topic_weights.json`
5. Commit changes

The system will incorporate your perspective into every future analysis.

---

## Step 10: Set Your Analysis Schedule

The system runs automatically by default (twice daily at 6am and 6pm UTC).

To change the schedule:
1. Navigate to `config/schedules.yaml`
2. Edit the `primary_schedule` value
3. Commit changes

OR edit `.github/workflows/intelligence.yml` directly.

---

## Troubleshooting

### "Pipeline Failed" in Actions

1. Click the failed run to see the error details
2. Most common issues:

**"ANTHROPIC_API_KEY is not set"**
→ Re-check Step 4. The secret name must be exactly `ANTHROPIC_API_KEY`.

**"No module named feedparser"**
→ The requirements.txt didn't install. Check the "Install Dependencies" step in Actions logs.

**"Rate limit exceeded"**
→ Your Anthropic API usage limit was hit. Check your limits at console.anthropic.com.
→ Or reduce `stories_per_run` in `config/schedules.yaml`.

**"No articles to rank"**
→ All feeds failed or returned no recent articles. Check `config/feeds.yaml` for valid URLs.

### GitHub Pages Not Loading

1. Confirm Pages is set to "GitHub Actions" source (not a branch)
2. The first deployment takes 5-10 minutes after the pipeline completes
3. Check the "Pages" section in Settings for deployment status

### Chatbot Not Working

1. Make sure you entered your API key in the chatbot setup
2. The key must start with `sk-ant-`
3. Check that you have credit/billing set up at console.anthropic.com

---

## Operating Costs

| Item | Cost |
|------|------|
| GitHub | Free (public repo) |
| GitHub Pages | Free |
| GitHub Actions | ~2,000 free minutes/month (well within limits) |
| Anthropic API | ~$0.05-0.25 per story analysis (varies by model/length) |
| **Total for 5 stories/day** | **~$5-30/month** |

To control costs:
- Reduce `stories_per_run` in `config/schedules.yaml`
- Reduce `max_tokens_per_analysis` in `config/schedules.yaml`
- Run less frequently (change schedule)

---

## Advanced: Running Locally (Optional)

If you want to test the pipeline on your computer:

```bash
# 1. Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set your API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 4. Run the pipeline
python scripts/run_pipeline.py

# 5. Open a report
open reports/2024/01/01/*/index.html
```

---

## Getting Help

- Check the troubleshooting section above
- Look at the GitHub Actions run logs for detailed error messages
- Read `ARCHITECTURE.md` for technical details
- File issues at: [github.com/YOUR_USERNAME/YOUR_REPO/issues]

---

*You've set up a fully autonomous intelligence system. It will run twice daily, generate reports, accumulate knowledge, and get smarter over time — all automatically.*

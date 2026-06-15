# GitHub Setup Guide

This guide will help you upload the SO3 project to GitHub.

## 📋 Prerequisites

- Git installed on your computer
- GitHub account created
- Command line access (PowerShell, Git Bash, or Terminal)

## 🚀 Step-by-Step Instructions

### 1. Initialize Git Repository

Open PowerShell/Terminal in the SO3 folder:

```powershell
cd C:\Users\JanChristopherRobinB\Desktop\SO3
git init
```

### 2. Configure Git (First Time Only)

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@dlsu.edu.ph"
```

### 3. Add All Files

```powershell
git add .
```

This will add all files except those listed in `.gitignore`.

### 4. Create Initial Commit

```powershell
git commit -m "Initial commit: SO3 FPGA Chaos Synchronization implementation"
```

### 5. Create GitHub Repository

1. Go to https://github.com
2. Click the **"+"** icon (top right) → **"New repository"**
3. Fill in:
   - **Repository name**: `fpga-chaos-sync-so3` (or your preferred name)
   - **Description**: `FPGA implementation of Pecora-Carroll chaos synchronization for thesis SO3`
   - **Visibility**: Choose **Public** or **Private**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

### 6. Link Local Repository to GitHub

Copy the commands from GitHub's "push an existing repository" section, or use:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/fpga-chaos-sync-so3.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### 7. Verify Upload

1. Refresh your GitHub repository page
2. You should see all folders and files:
   ```
   ├── hdl/
   ├── scripts/
   ├── constraints/
   ├── python/
   ├── docs/
   ├── .gitignore
   ├── LICENSE
   ├── README.md
   ├── QUICKSTART.md
   └── GITHUB_SETUP.md
   ```

## 📝 Future Updates

When you make changes to files:

```powershell
# Check what changed
git status

# Add specific files
git add path/to/file.vhd

# Or add all changes
git add .

# Commit with descriptive message
git commit -m "Description of changes"

# Push to GitHub
git push
```

## 🔒 Using SSH Instead of HTTPS (Optional but Recommended)

### Generate SSH Key

```powershell
ssh-keygen -t ed25519 -C "your.email@dlsu.edu.ph"
```

Press Enter to accept default location, optionally set a passphrase.

### Add SSH Key to GitHub

1. Copy your public key:
   ```powershell
   cat ~/.ssh/id_ed25519.pub
   ```
2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the key and save

### Change Remote to SSH

```powershell
git remote set-url origin git@github.com:YOUR_USERNAME/fpga-chaos-sync-so3.git
```

## 📂 What Gets Uploaded

✅ **Included** (tracked by Git):
- All VHDL source files (`hdl/`)
- Python scripts (`python/`)
- TCL scripts (`scripts/`)
- Constraints (`constraints/`)
- Documentation (`docs/`, `*.md`)
- License file

❌ **Excluded** (in `.gitignore`):
- Vivado project files (`vivado_project/`)
- Generated bitstreams (`*.bit`)
- Python cache (`__pycache__/`)
- Data files (`*.csv`, `analysis_results/`)
- OS files (`.DS_Store`, `Thumbs.db`)

## 🎯 Repository Settings (Optional)

### Add Topics

On GitHub repository page:
1. Click ⚙️ (Settings icon) next to "About"
2. Add topics: `fpga`, `vhdl`, `chaos-theory`, `pynq`, `zynq`, `synchronization`, `thesis`

### Add Description

In the same "About" section:
```
FPGA implementation of Pecora-Carroll chaos synchronization using Rossler oscillator on PYNQ-Z2 boards. Part of DLSU ECE thesis on chaos-based secure communication.
```

### Enable GitHub Pages (for documentation)

1. Settings → Pages
2. Source: Deploy from branch
3. Branch: `main`, folder: `/docs`
4. Save

Your documentation will be available at:
`https://YOUR_USERNAME.github.io/fpga-chaos-sync-so3/`

## 🤝 Collaboration

### Add Collaborators

If working with teammates:
1. Repository → Settings → Collaborators
2. Add by GitHub username or email

### Branch Protection (Optional)

For team projects:
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable: "Require pull request reviews before merging"

## 📊 GitHub Features to Use

### Issues

Track bugs, enhancements, or thesis tasks:
- Repository → Issues → New issue

### Projects

Organize thesis milestones:
- Repository → Projects → New project

### Releases

When completing major milestones:
1. Repository → Releases → Create a new release
2. Tag: `v1.0-so3-complete`
3. Title: "SO3 Implementation Complete"
4. Description: Summary of deliverables

## 🆘 Troubleshooting

### "Permission denied (publickey)"

Use HTTPS instead of SSH, or set up SSH keys properly.

### "Repository not found"

Check repository name and your GitHub username in the URL.

### Large files rejected

Ensure `.gitignore` is working. Check file sizes:
```powershell
git ls-files -s | sort -k4 -n -r | head -20
```

### Undo last commit (before push)

```powershell
git reset --soft HEAD~1
```

### Remove file from Git but keep locally

```powershell
git rm --cached filename
```

## 📧 Need Help?

- GitHub Docs: https://docs.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf
- DLSU IT Support: [contact info]

---

**Ready to push to GitHub!** 🚀

Follow steps 1-7 above to get your SO3 project online.
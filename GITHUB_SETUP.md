# Simple Agent Base - Repository Setup

## GitHub Repository Setup Instructions

After creating a repository on GitHub, run these commands:

```powershell
# Add the remote repository (replace YOUR_USERNAME and YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push the current branch to GitHub
git branch -M main
git push -u origin main
```

## Example Commands
If your GitHub username is 'yourname' and repository is 'simple-agent-base':

```powershell
git remote add origin https://github.com/yourname/simple-agent-base.git
git branch -M main
git push -u origin main
```

## Project Description for GitHub

**Simple Agent Base** - An AI agent framework with multi-tool support including data search, store information lookup, and user analysis capabilities. Built with Python, Streamlit, and LangChain.

### Key Features:
- 🔍 Data search across stores, events, and narrative data
- 🏪 Store information and hours lookup
- 📊 User interest analysis
- 🕐 Time and math utilities
- 🌐 Streamlit web interface
- 🔧 Extensible tool registry system

### Technologies:
- Python 3.11+
- Streamlit
- LangChain
- Anthropic Claude
- CSV/JSON data processing

### Recent Improvements:
- Fixed search functionality to support multiple keywords
- Enhanced tool registry with proper type annotations
- Added comprehensive verification and testing utilities
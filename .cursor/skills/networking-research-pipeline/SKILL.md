---
name: networking-research-pipeline
description: Integrated networking research workflow that leverages pipeline automation for GitHub analysis and manual research for non-GitHub platforms, eliminating duplicate work and reducing token burn.
license: MIT
compatibility: Requires access to pipeline tools and research indices.
metadata:
  author: hermes-agent
  version: "1.0"
  generatedBy: "hermes-2.0"
---

## Overview

This skill provides a comprehensive networking research workflow that combines automated pipeline analysis (GitHub) with targeted manual research (non-GitHub platforms) to create integrated research indices without duplicate work.

## When to Use

- Researching companies for networking opportunities
- Building target lists for outreach campaigns
- Analyzing technical teams and their contributions
- Creating comprehensive company research profiles

## Workflow

### 1. Automated Pipeline Analysis (GitHub)
```bash
# Run pipeline GitHub analysis
python pipeline/find_rl_people.py --company "Acme Corp"
python pipeline/resolve_github.py --company "Acme Corp"
python pipeline/find_oss_contributions.py --company "Acme Corp"
```

### 2. Manual Research (Non-GitHub Platforms)
```bash
# Focus on platforms where human judgment adds value
- LinkedIn profiles (Chrome extension)
- Company websites and job postings
- Twitter/X research and news articles
- Culture assessment and recruiter identification
```

### 3. Integrated Research Index Generation
```python
# Auto-generate combined research index
def generate_research_index(company_name):
    """Combine manual research + pipeline GitHub data"""
    manual_profiles = load_manual_profiles(company_name)
    pipeline_people = load_pipeline_github_data(company_name)
    
    return f"""# {company_name} - Integrated Research Index

## Manual Research (Non-GitHub)
- LinkedIn Profiles: {len(manual_profiles)}
- Key Roles: {extract_titles(manual_profiles)}
- Culture Insights: [From manual research]

## Pipeline GitHub Analysis  
- GitHub Members: {len(pipeline_people)}
- OSS Contributions: {count_oss_contributions(pipeline_people)}
- Active Repositories: {count_active_repos(pipeline_people)}

## Combined View
### Leadership & Key Roles (Manual)
{format_manual_people(manual_profiles)}

### Technical Contributors (GitHub)  
{format_github_people(pipeline_people)}

## Strategic Recommendations
- Engage: [Manual research targets] + [Top GitHub contributors]
- Focus: Areas with both manual and GitHub signal
"""
```

## Key Features

### Efficiency Optimization
- **No duplicate GitHub scanning**: Pipeline handles all GitHub analysis
- **Reduced token burn**: Manual research focuses on human-centric platforms
- **Structured output**: Automated integration of both data sources

### Pipeline Integration
- Leverages existing `find_rl_people.py`, `resolve_github.py`, `find_oss_contributions.py`
- Enhanced GitHub person-organization matching
- Activity-based prioritization of contributors

### Manual Research Focus
- LinkedIn profile analysis (Chrome extension)
- Company website research
- Job posting analysis (Greenhouse/Lever APIs)
- Culture and team structure assessment

## Configuration

### Environment Variables
```bash
# GitHub API (already configured in pipeline)
export GITHUB_TOKEN=your_token

# Optional: Google Search API for job postings
export GOOGLE_PAID_SEARCH_API_KEY=your_key
```

### Research Conventions
- Manual research files: `research/{company}/profiles.json`
- Pipeline output: `pipeline/output/{company}/github_people.json`
- Generated indices: `research/{company}/index.md`

## Examples

### Basic Company Research
```bash
# Research Acme Corp
research-company "Acme Corp"
```

### Targeted Role Research
```bash
# Focus on engineering leadership
research-company "Acme Corp" --roles "CTO,VP Engineering,Principal Engineer"
```

### Tech Stack Analysis
```bash
# Include technology focus
research-company "Acme Corp" --technologies "python,kubernetes,react"
```

## Pitfalls to Avoid

### ❌ Don't manually scan GitHub
- The pipeline already handles GitHub analysis comprehensively
- Manual GitHub scanning creates duplicate work and burns tokens

### ❌ Don't mix research methods
- Keep manual research focused on non-GitHub platforms
- Let pipeline handle technical GitHub analysis

### ✅ Do use structured templates
- Use consistent research index templates
- Maintain clear separation of data sources

### ✅ Do validate pipeline integration
- Ensure pipeline GitHub data is properly integrated
- Verify person-organization matching accuracy

## Verification

### Quality Checks
- Manual research should contain no GitHub analysis
- Pipeline output should enhance manual research, not duplicate it
- Research indices should show clear integration of both sources
- No token burn on GitHub scraping in manual research

### Performance Metrics
- Time saved by eliminating duplicate GitHub work
- Token reduction from avoiding agentic GitHub scraping
- Quality improvement from specialized platform focus

## Related Skills

- `job-search-automation`: For automated job posting discovery
- `company-research`: For broader company analysis
- `github-analysis`: For detailed GitHub contribution analysis

## Version History

- v1.0: Initial skill creation with integrated pipeline-manual workflow
- Focus on eliminating duplicate GitHub scanning and reducing token burn

This skill represents a significant efficiency improvement by properly dividing labor between automated pipeline analysis and targeted manual research, eliminating duplicate work and reducing LLM token consumption.
# 🔄 Alternative API Options

Avoid Claude's $5 minimum charge! Use these FREE or pay-per-use alternatives:

## 🆓 Option 1: Google Gemini (RECOMMENDED - FREE!)

### Pricing
- **FREE Tier**: 15 requests/minute, 1500 requests/day
- **Paid**: $0.50 per 1M tokens (20x cheaper than Claude direct)

### Setup

**1. Get FREE API Key:**
```
Visit: https://makersuite.google.com/app/apikey
Click: "Create API Key"
Copy your key
```

**2. Install Dependencies:**
```bash
pip install -r requirements_gemini.txt
```

**3. Configure:**
```bash
copy config\.env.gemini config\.env
# Edit config\.env and add your Gemini API key
```

**4. Update main.py:**
```python
# Change line in src/main.py:
from src.agents.vision_agent_gemini import VisionAgentGemini as VisionAgent

# Initialize:
vision_agent = VisionAgent(api_key=os.getenv("GEMINI_API_KEY"))
```

**5. Run:**
```bash
python src\main.py
```

### Pros
✅ FREE tier (1500 requests/day)
✅ No credit card required for free tier
✅ Fast response times
✅ Good accuracy (90%+)
✅ Easy setup

### Cons
❌ Rate limited (15 req/min on free tier)
❌ Slightly less accurate than Claude

---

## 💰 Option 2: AWS Bedrock (Pay-per-use, No Minimum)

### Pricing
- **No minimum charge** (unlike Claude direct)
- **Pay-per-use**: ~$3 per 1M tokens
- Only pay for what you use

### Setup

**1. AWS Account:**
```
Sign up: https://aws.amazon.com/
Enable Bedrock: https://console.aws.amazon.com/bedrock/
Request model access (Claude 3.5 Sonnet)
```

**2. Configure AWS CLI:**
```bash
pip install awscli
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)
```

**3. Install Dependencies:**
```bash
pip install -r requirements_bedrock.txt
```

**4. Configure:**
```bash
copy config\.env.bedrock config\.env
```

**5. Update main.py:**
```python
# Change line in src/main.py:
from src.agents.vision_agent_bedrock import VisionAgentBedrock as VisionAgent

# Initialize:
vision_agent = VisionAgent(region=os.getenv("AWS_REGION", "us-east-1"))
```

**6. Run:**
```bash
python src\main.py
```

### Pros
✅ No minimum charge
✅ Pay only for what you use
✅ Same Claude model quality
✅ AWS infrastructure reliability
✅ Better for production

### Cons
❌ Requires AWS account setup
❌ More complex configuration
❌ Need to manage AWS credentials

---

## 📊 Cost Comparison (1000 screenshots)

| Provider | Setup Cost | Per 1000 Screenshots | Total |
|----------|-----------|---------------------|-------|
| **Claude Direct** | $5 minimum | ~$2 | **$7** |
| **AWS Bedrock** | $0 | ~$2 | **$2** |
| **Google Gemini FREE** | $0 | $0 | **$0** |
| **Google Gemini Paid** | $0 | ~$0.30 | **$0.30** |

---

## 🎯 Recommendation

### For Testing/Personal Use:
**Use Google Gemini FREE tier**
- No cost
- Easy setup
- 1500 screenshots/day limit

### For Production:
**Use AWS Bedrock**
- No minimum charge
- Better reliability
- Same Claude quality

---

## 🚀 Quick Start (Gemini FREE)

```bash
# 1. Get API key from https://makersuite.google.com/app/apikey
# 2. Install
pip install -r requirements_gemini.txt

# 3. Configure
copy config\.env.gemini config\.env
# Add your GEMINI_API_KEY

# 4. Run
python src\main.py
```

**That's it! No credit card, no $5 charge!**

---

## 🔧 Switching Between Providers

The project supports all three providers. Just:
1. Use the appropriate requirements file
2. Use the appropriate .env template
3. Import the correct vision agent in main.py

All agents have the same interface, so switching is easy!

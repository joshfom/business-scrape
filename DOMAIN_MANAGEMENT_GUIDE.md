# 🌐 Domain Management Guide

## How to Update Domain URLs in Business Scraper

This guide explains how to properly change, add, or update domain URLs in the Business Scraper system.

---

## 📍 **Where Domain List is Located**

**Primary File**: `backend/api/endpoints/scraping.py`  
**Function**: `get_available_domains()`  
**Line Range**: ~280-350

---

## 🔧 **Step-by-Step Process to Update Domains**

### 1. **Edit the Domain List**
Open: `backend/api/endpoints/scraping.py`

Find the `ALL_DOMAINS` array inside the `get_available_domains()` function:

```python
ALL_DOMAINS = [
    # Asia
    {'domain': 'https://armeniayp.com', 'country': 'Armenia'},
    
    # Middle East  
    {'domain': 'https://www.yello.ae', 'country': 'UAE'},
    
    # Africa
    {'domain': 'https://www.businesslist.com.ng/', 'country': 'Nigeria'},  # ✅ Updated
    
    # Add new domains here...
]
```

### 2. **Required Steps After Making Changes**

#### ⚠️ **CRITICAL**: You MUST restart the backend for changes to take effect

```bash
# Method 1: Using process management
pkill -f "uvicorn main:app"
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Method 2: Using utility scripts
./stop_app.sh
./start_app.sh

# Method 3: VS Code Tasks
# Ctrl+Shift+P -> "Tasks: Run Task" -> "Start Backend API"
```

### 3. **Verify Changes**

```bash
# Test if backend is running
curl -s "http://localhost:8000/health"

# Check specific domain update
curl -s "http://localhost:8000/api/scraping/available-domains" | grep -A3 -B1 "Nigeria"

# Full domain list (formatted)
curl -s "http://localhost:8000/api/scraping/available-domains" | jq '.available_domains'
```

### 4. **Frontend Refresh**
The frontend automatically fetches the updated domain list from the API, but you may need to:
- Refresh the browser page (F5)
- Clear browser cache if needed
- The dropdown will show updated domains immediately

---

## 📝 **Domain Format Requirements**

### ✅ **Correct Format**
```python
{'domain': 'https://www.businesslist.com.ng/', 'country': 'Nigeria'}
```

### 📋 **Format Rules**
- **Protocol**: Must include `https://` or `http://`
- **Country**: Use proper country name (not country code)
- **Trailing Slash**: Include if the website requires it
- **www**: Include if the website uses it

### ❌ **Common Mistakes**
```python
# Missing protocol
{'domain': 'businesslist.com.ng', 'country': 'Nigeria'}

# Wrong country format  
{'domain': 'https://www.businesslist.com.ng/', 'country': 'NG'}

# Inconsistent formatting
{'domain': 'businesslist.com.ng/', 'country': 'Nigeria'}
```

---

## 🔍 **Recent Fix Example**

### **Nigeria Domain Update**
```python
# ❌ Before (Wrong URL)
{'domain': 'https://nigeriayp.com', 'country': 'Nigeria'}

# ✅ After (Correct URL)  
{'domain': 'https://www.businesslist.com.ng/', 'country': 'Nigeria'}
```

**Steps Taken:**
1. ✅ Updated domain in `ALL_DOMAINS` array
2. ✅ Restarted backend service
3. ✅ Verified change with API call
4. ✅ Confirmed frontend reflects the change

---

## 🆕 **Adding New Domains**

### **Template for New Domain**
```python
# Add to appropriate geographical section
{'domain': 'https://example-business-directory.com', 'country': 'Country Name'},
```

### **Geographical Sections Available**
- **Asia**: Asian countries
- **Middle East**: Gulf and Middle Eastern countries  
- **Africa**: African countries
- **Europe**: European countries (can be added)
- **Americas**: North/South American countries (can be added)

### **Example Addition**
```python
# Africa section
{'domain': 'https://egyptyp.com', 'country': 'Egypt'},
{'domain': 'https://www.businesslist.com.ng/', 'country': 'Nigeria'},
{'domain': 'https://kenyabusinessdirectory.com', 'country': 'Kenya'},  # New addition
```

---

## 🛠️ **Testing New Domains**

### **1. API Verification**
```bash
# Check domain appears in available list
curl -s "http://localhost:8000/api/scraping/available-domains" | jq '.available_domains[] | select(.country == "Nigeria")'

# Check total domain count
curl -s "http://localhost:8000/api/scraping/available-domains" | jq '.total_domains'
```

### **2. Frontend Testing**
1. Navigate to: http://localhost:3020/jobs
2. Click "New Job" 
3. Check domain dropdown includes updated domain
4. Verify country name displays correctly

### **3. Scraping Test**
1. Create a test job with the new domain
2. Verify the scraper can access the website
3. Check if the website structure is compatible

---

## ⚡ **Quick Reference Commands**

### **View Current Domains**
```bash
# List all domains with countries
curl -s "http://localhost:8000/api/scraping/available-domains" | jq '.available_domains[] | "\(.country): \(.domain)"'

# Count by region (manual grouping needed)
curl -s "http://localhost:8000/api/scraping/available-domains" | jq '.available_domains | length'
```

### **Restart Services**
```bash
# Quick restart
./stop_app.sh && ./start_app.sh

# Check service status
./check_services.sh
```

### **View Logs for Debugging**
```bash
# Backend logs
tail -f logs/backend.log

# Or direct output
cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🚨 **Troubleshooting**

### **Problem**: Domain change not reflecting in frontend
**Solution**: 
1. ✅ Verify backend restart
2. ✅ Clear browser cache
3. ✅ Check API response manually
4. ✅ Refresh frontend page

### **Problem**: Backend won't start after domain change
**Solution**:
1. Check syntax errors in the domain list
2. Ensure proper comma placement
3. Verify all quotes are properly closed
4. Check backend logs for specific errors

### **Problem**: New domain doesn't work for scraping
**Solution**:
1. Verify the website exists and is accessible
2. Check if the website structure matches expected format
3. Test website accessibility from server
4. Update scraper logic if needed for new site structure

---

## 📊 **Current Domain Statistics**
- **Total Domains**: 50+ business directories
- **Regions Covered**: Asia, Middle East, Africa
- **Most Recent Update**: Nigeria - corrected to `https://www.businesslist.com.ng/`

---

**⚠️ Remember**: Always restart the backend after making domain changes!

# 🔧 Troubleshooting Guide

## Common Issues

### 1. CSS Selectors Not Working
**Problem:** Data not being extracted correctly
**Solution:** 
- Use browser dev tools (F12) to find correct selectors
- Test selectors in browser console: `document.querySelector('.selector')`
- Update selectors in config file

### 2. Being Blocked by Websites
**Problem:** Getting 403/429 errors
**Solution:**
- Increase delay ranges in config
- Rotate user agents
- Use proxy servers
- Respect robots.txt

### 3. Email Not Sending
**Problem:** Reports not being emailed
**Solution:**
- Use app passwords for Gmail
- Check SMTP settings
- Verify firewall settings
- Test email configuration

### 4. Installation Issues
**Problem:** Requirements installation fails
**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 5. Permission Errors
**Problem:** Cannot write files
**Solution:**
- Check folder permissions
- Run as administrator (Windows)
- Use `chmod` to fix permissions (Linux/Mac)

## Debug Tips

1. **Check logs:** `logs/scraping_bot.log`
2. **Test single product** before bulk scraping
3. **Verify selectors** in browser first
4. **Start with demo sites** like books.toscrape.com

## Getting Help

1. Check the logs for error details
2. Test configuration step by step
3. Verify network connectivity
4. Update selectors for website changes

# 📖 Admin Panel Quick Reference

## 🚀 Quick Access

| Feature | URL | Shortcut |
|---------|-----|----------|
| Admin Home | `/admin/` | Click logo |
| Dashboard | `/admin/dashboard/` | Top menu: "📊 داشبورد" |
| Users | `/admin/users/profile/` | Left menu: Profiles |
| Orders | `/admin/trading/order/` | Left menu: Orders |
| Transactions | `/admin/trading/transaction/` | Left menu: Transactions |
| Products | `/admin/trading/product/` | Left menu: Products |

---

## 🎯 Common Tasks

### Approve New Users
1. Go to **Users** → **Profiles**
2. Filter by: `is_approved = False`
3. Select users
4. Action: **"تأیید کاربران انتخاب شده"**
5. Click **Go**

### Process Pending Orders
1. Go to **Trading** → **Orders**
2. Filter by: `Status = PENDING`
3. Check user balances (✓ indicator)
4. Select orders
5. Action: **"تکمیل سفارشات انتخاب شده"**
6. Click **Go**

### Approve Deposit Transactions
1. Go to **Trading** → **Transactions**
2. Filter by: `Status = PENDING`, `Type = DEPOSIT`
3. View receipt by clicking **"📷 مشاهده رسید"**
4. Select verified transactions
5. Action: **"تأیید واریزهای انتخاب شده"**
6. Click **Go**

### Process Withdrawals
1. Go to **Trading** → **Withdraw Requests**
2. Filter by: `Status = PENDING`
3. Check frozen balances (✓ indicator)
4. Select requests
5. Action: **"پردازش برداشت‌های انتخاب شده"**
6. Click **Go**

### Update Product Prices
1. Go to **Trading** → **Products**
2. Edit prices directly in list view (inline editing)
3. Click **Save**

### Export Data
1. Go to any model list (e.g., Orders)
2. Click **"Export"** button at top
3. Choose format: Excel, CSV, JSON
4. Click **"Export"**

### View Audit Log
1. Go to any model change page
2. Scroll to **"History"** section
3. View all changes with timestamps and users

---

## 🎨 Status Badge Colors

| Status | Color | Meaning |
|--------|-------|---------|
| 🟢 Green | Success | Completed, Approved, Verified |
| 🟡 Yellow | Warning | Pending, Waiting |
| 🔵 Blue | Info | Processing, In Progress |
| 🔴 Red | Danger | Rejected, Cancelled, Error |
| ⚫ Gray | Secondary | Inactive, Disabled |

---

## 📊 Dashboard Sections

### Main KPIs (Top Row)
- **Total Users:** All registered users with weekly growth
- **Pending Orders:** Orders awaiting processing
- **Pending Transactions:** Transactions awaiting approval
- **Total Revenue:** Revenue from completed sales

### Detailed Stats
- **User Statistics:** Total, approved, pending, new
- **Order Statistics:** Total, completed, pending, cancelled
- **Transaction Statistics:** Deposits, withdrawals, pending
- **Financial Statistics:** Revenue, costs, deposits, withdrawals

### Recent Activity
- **Latest Orders:** Last 10 orders with status
- **Recent Transactions:** Last 10 transactions
- **New Users:** Last 10 user registrations

### Alerts
- Red/Yellow alerts for pending items requiring action
- Click **"مشاهده"** to go directly to filtered list

---

## 🔍 Advanced Filtering

### Date Range Filters
1. Click on date filter (e.g., "Created date")
2. Select **"Custom date range"**
3. Choose start and end dates
4. Click **Apply**

### Numeric Range Filters
1. Click on numeric filter (e.g., "Balance")
2. Enter min and max values
3. Click **Apply**

### Multiple Filters
- Apply multiple filters simultaneously
- Filters are combined with AND logic
- Clear filters: Click **"Clear all filters"**

---

## 💾 Import/Export

### Export Current View
1. Apply filters as needed
2. Click **"Export"** button
3. Choose format
4. Download file

### Import Data
1. Click **"Import"** button
2. Choose file (CSV, Excel, etc.)
3. Map columns (if needed)
4. Preview import
5. Confirm import

---

## 🔐 Security Features

### Masked Data
- Bank account numbers show only last 4 digits
- Full numbers visible in detail view only

### Audit Trail
- All changes are logged
- View who changed what and when
- Access via model history

### Permissions
- Dashboard respects user permissions
- Staff users can only see allowed sections
- Superusers see everything

---

## ⚡ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Search | `/` (forward slash) |
| Save | `Ctrl/Cmd + S` |
| Save and continue | `Ctrl/Cmd + Shift + S` |
| Navigate search | `Tab` |

---

## 🎨 Customization

### Change Theme
Edit `gold_shop/settings.py`:
```python
JAZZMIN_SETTINGS = {
    "theme": "flatly",  # Change theme name
}
```

Available themes:
- default, darkly, flatly, journal, litera, lux, materia, minty, pulse, sandstone, simplex, slate, spacelab, superhero, united, yeti

### Change Language
Edit `gold_shop/settings.py`:
```python
LANGUAGE_CODE = 'fa-ir'  # Persian
TIME_ZONE = 'Asia/Tehran'
```

---

## 🐛 Common Issues

### "Static files not found"
```bash
python manage.py collectstatic
```

### "Dashboard not loading"
Check URL: Should be `/admin/dashboard/` (with trailing slash)

### "Import fails"
- Check file format matches selected type
- Ensure headers match field names
- Verify data types are correct

### "Filters not working"
- Clear browser cache
- Reload page
- Check if rangefilter package is installed

---

## 📱 Mobile Access

The admin panel is fully responsive:
- Works on tablets and smartphones
- Touch-optimized controls
- Simplified navigation on small screens
- All features available on mobile

---

## 📞 Quick Help

1. **Documentation:** See `ADMIN_PANEL_ENHANCEMENTS.md`
2. **Django Docs:** https://docs.djangoproject.com/en/4.2/
3. **Jazzmin Docs:** https://django-jazzmin.readthedocs.io/

---

## 🎯 Pro Tips

1. **Use keyboard shortcuts** for faster navigation
2. **Apply filters before export** to get specific data
3. **Use inline editing** for quick price updates
4. **Check dashboard daily** for pending items
5. **Review audit logs** for suspicious activity
6. **Export data regularly** for backups
7. **Use date ranges** to analyze specific periods
8. **Bookmark common filters** in browser

---

## ✅ Daily Checklist

- [ ] Check dashboard for alerts
- [ ] Process pending orders
- [ ] Approve deposit transactions
- [ ] Handle withdrawal requests
- [ ] Verify new users
- [ ] Review system statistics
- [ ] Check for suspicious activity

---

**Last Updated:** 2025-11-03
**Version:** 2.0

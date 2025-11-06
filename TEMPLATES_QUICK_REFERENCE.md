# 🚀 Templates Quick Reference Guide

## 📚 Quick Links
- [Full Documentation](templates/README.md)
- [Enhancement Summary](TEMPLATE_ENHANCEMENTS.md)

---

## 🎨 CSS Files

### Load All Required Styles
```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/base.css' %}">
<link rel="stylesheet" href="{% static 'css/components.css' %}">
<link rel="stylesheet" href="{% static 'css/dashboard.css' %}">  <!-- For dashboards -->
<link rel="stylesheet" href="{% static 'css/home.css' %}">       <!-- For landing pages -->
<link rel="stylesheet" href="{% static 'css/layout.css' %}">     <!-- For layouts -->
```

---

## 🧩 Component Quick Reference

### KPI Card
```django
{% include 'components/kpi_card.html' with 
    icon="📊"
    title="Total Users"
    value=1234
    subtitle="10 new this week"
    variant="primary"
%}
```
**Variants:** `primary` `success` `warning` `info` `gold` `purple`

### Alert
```django
{% include 'components/alert.html' with 
    type="success"
    icon="✓"
    message="Success!"
    dismissible=True
%}
```
**Types:** `success` `warning` `danger` `info`

### Card
```django
{% include 'components/card.html' with 
    title="Title"
    content="Content"
    hover=True
%}
```

### Stat Card
```django
{% include 'components/stat_card.html' with 
    icon="👥"
    title="Statistics"
    stats=stats_list
%}
```
**Stats format:**
```python
stats = [
    {'label': 'Label', 'value': 123},
]
```

### Activity Item
```django
{% include 'components/activity_item.html' with 
    icon="👤"
    icon_bg="success"
    title="Title"
    description="Description"
    time="2h ago"
%}
```

### Empty State
```django
{% include 'components/empty_state.html' with 
    icon="📭"
    title="No Data"
    description="Nothing here"
%}
```

---

## 🎯 CSS Variables

### Colors
```css
var(--primary-color)      /* #d4af37 - Gold */
var(--success-color)      /* #4caf50 - Green */
var(--warning-color)      /* #ffc107 - Yellow */
var(--danger-color)       /* #dc3545 - Red */
var(--info-color)         /* #17a2b8 - Blue */
var(--text-primary)       /* #2c3e50 */
var(--text-secondary)     /* #666666 */
var(--background)         /* #f5f5f5 */
var(--surface)            /* #ffffff */
var(--border-color)       /* #e0e0e0 */
```

### Spacing
```css
var(--spacing-xs)   /* 0.25rem - 4px */
var(--spacing-sm)   /* 0.5rem  - 8px */
var(--spacing-md)   /* 1rem    - 16px */
var(--spacing-lg)   /* 1.5rem  - 24px */
var(--spacing-xl)   /* 2rem    - 32px */
var(--spacing-2xl)  /* 3rem    - 48px */
```

### Shadows
```css
var(--shadow-sm)    /* Subtle shadow */
var(--shadow-md)    /* Medium shadow */
var(--shadow-lg)    /* Large shadow */
var(--shadow-xl)    /* Extra large shadow */
```

### Border Radius
```css
var(--radius-sm)    /* 0.25rem */
var(--radius-md)    /* 0.5rem */
var(--radius-lg)    /* 0.75rem */
var(--radius-xl)    /* 1rem */
```

---

## 🎨 Utility Classes

### Flexbox
```html
<div class="d-flex justify-content-center align-items-center">
```
- `d-flex` - Display flex
- `flex-column` - Column direction
- `justify-content-center` - Center horizontally
- `justify-content-between` - Space between
- `align-items-center` - Center vertically

### Grid
```html
<div class="grid grid-cols-3">
```
- `grid` - Display grid
- `grid-cols-1` to `grid-cols-4` - Column count

### Spacing
```html
<div class="mt-2 mb-3 p-2">
```
- `mt-1` `mt-2` `mt-3` - Margin top
- `mb-1` `mb-2` `mb-3` - Margin bottom
- `p-1` `p-2` `p-3` - Padding

### Text
```html
<p class="text-center text-primary">
```
- `text-center` `text-left` `text-right`
- `text-primary` `text-secondary` `text-muted`
- `text-success` `text-warning` `text-danger` `text-info`

### Buttons
```html
<button class="btn btn-primary btn-lg">
```
**Variants:**
- `btn-primary` `btn-secondary` `btn-success`
- `btn-warning` `btn-danger` `btn-outline`

**Sizes:**
- `btn-sm` `btn-lg`

### Badges
```html
<span class="badge badge-success">
```
**Types:**
- `badge-success` `badge-warning` `badge-danger`
- `badge-info` `badge-primary` `badge-secondary`

---

## 📱 Responsive Breakpoints

```css
/* Mobile First */
.class { }                    /* Mobile: < 768px */

@media (min-width: 769px) { } /* Tablet: 769px - 1024px */
@media (min-width: 1025px) { } /* Desktop: > 1024px */
```

---

## 🚀 JavaScript API

### Dashboard
```javascript
// Manual refresh
window.Dashboard.refresh();

// Toggle auto-refresh
window.Dashboard.toggleAutoRefresh(true);
```

---

## 🎨 Common Patterns

### Page Layout
```django
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
{% endblock %}

{% block content %}
<div class="container">
    <!-- Your content -->
</div>
{% endblock %}

{% block extra_scripts %}
<script src="{% static 'js/custom.js' %}"></script>
{% endblock %}
```

### KPI Dashboard
```django
<div class="kpi-grid">
    {% include 'components/kpi_card.html' with icon="👥" title="Users" value=users variant="primary" %}
    {% include 'components/kpi_card.html' with icon="💰" title="Revenue" value=revenue variant="gold" %}
    {% include 'components/kpi_card.html' with icon="📊" title="Orders" value=orders variant="info" %}
</div>
```

### Stats Section
```django
<div class="stats-grid">
    {% include 'components/stat_card.html' with icon="👥" title="User Stats" stats=user_stats %}
    {% include 'components/stat_card.html' with icon="💰" title="Finance Stats" stats=finance_stats %}
</div>
```

### Activity Feed
```django
<div class="activity-feed">
    <div class="activity-feed-header">
        <h3>Recent Activity</h3>
    </div>
    <div class="activity-list">
        {% for item in activities %}
        {% include 'components/activity_item.html' with icon="🔔" title=item.title time=item.time %}
        {% endfor %}
    </div>
</div>
```

### Empty State
```django
{% if items %}
    <!-- Show items -->
{% else %}
    {% include 'components/empty_state.html' with icon="📭" title="No Items" %}
{% endif %}
```

---

## ⚡ Performance Tips

1. **Load CSS in `<head>`**
```django
{% block extra_css %}
<link rel="stylesheet" href="...">
{% endblock %}
```

2. **Load JS before `</body>`**
```django
{% block extra_scripts %}
<script src="..." defer></script>
{% endblock %}
```

3. **Use CSS Variables**
```css
.custom { color: var(--primary-color); }
```

4. **Leverage Utility Classes**
```html
<div class="d-flex mt-2 p-3 shadow rounded-lg">
```

---

## ♿ Accessibility Checklist

- ✅ Use semantic HTML (`header`, `main`, `nav`, etc.)
- ✅ Add `aria-label` to icon-only buttons
- ✅ Include skip link: `<a href="#main-content" class="sr-only">`
- ✅ Use `role` attributes where needed
- ✅ Add `alt` text to images
- ✅ Ensure keyboard navigation works
- ✅ Test with screen reader

---

## 🐛 Common Issues

### Issue: Styles not loading
**Solution:**
```django
{% load static %}  <!-- Add at top -->
<link rel="stylesheet" href="{% static 'css/base.css' %}">
```

### Issue: Components not rendering
**Solution:**
- Check component path: `templates/components/`
- Verify all required parameters are passed
- Check for typos in component names

### Issue: JavaScript not working
**Solution:**
```django
<script src="{% static 'js/dashboard.js' %}" defer></script>
<!-- Add 'defer' attribute -->
```

### Issue: Layout breaks on mobile
**Solution:**
- Use responsive utility classes
- Test with browser dev tools
- Check media queries

---

## 📞 Need Help?

1. Check [Full Documentation](templates/README.md)
2. Review [Enhancement Summary](TEMPLATE_ENHANCEMENTS.md)
3. Inspect existing template examples
4. Contact development team

---

## 🎓 Learning Resources

### CSS
- Learn about CSS Variables
- Understand Flexbox and Grid
- Study BEM naming convention

### Accessibility
- WCAG 2.1 Guidelines
- ARIA attributes
- Semantic HTML

### Django Templates
- Template inheritance
- Template tags and filters
- Static files handling

---

**Happy Coding! 🚀**

*Last Updated: 2025-11-04*

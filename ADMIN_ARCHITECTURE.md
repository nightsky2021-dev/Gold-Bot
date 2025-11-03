# 🏗️ Admin Panel Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ADMIN PANEL (Enhanced)                        │
│                     http://localhost:8000/admin/                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼──────────┐       ┌───────────▼──────────┐
        │   JAZZMIN THEME      │       │   CUSTOM DASHBOARD   │
        │   - Modern UI        │       │   - KPIs             │
        │   - RTL Support      │       │   - Statistics       │
        │   - Responsive       │       │   - Activity Feed    │
        │   - Custom Icons     │       │   - Smart Alerts     │
        └───────────┬──────────┘       └───────────┬──────────┘
                    │                               │
        ┌───────────┴───────────────────────────────┴───────────┐
        │                                                        │
┌───────▼──────────┐  ┌──────────────┐  ┌────────────────────┐
│  ENHANCED ADMINS │  │   FILTERS    │  │  IMPORT/EXPORT     │
│  - Profile       │  │   - Date     │  │  - CSV             │
│  - BankAccount   │  │   - Numeric  │  │  - Excel           │
│  - Product       │  │   - Status   │  │  - JSON            │
│  - Order         │  │   - Type     │  │  - YAML            │
│  - Transaction   │  │              │  │                    │
│  - WithdrawReq   │  │              │  │                    │
└───────┬──────────┘  └──────┬───────┘  └─────────┬──────────┘
        │                     │                     │
        └──────────┬──────────┴──────────┬──────────┘
                   │                     │
        ┌──────────▼─────────┐  ┌───────▼──────────┐
        │   AUDIT LOGGING    │  │  BULK ACTIONS    │
        │   - Track changes  │  │  - Approve       │
        │   - User actions   │  │  - Process       │
        │   - Timestamps     │  │  - Export        │
        │   - History view   │  │  - Update        │
        └──────────┬─────────┘  └───────┬──────────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   DJANGO MODELS    │
                    │   - Profile        │
                    │   - BankAccount    │
                    │   - Product        │
                    │   - Order          │
                    │   - Transaction    │
                    │   - WithdrawReq    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │     DATABASE       │
                    │   (SQLite/PG)      │
                    └────────────────────┘
```

---

## Component Breakdown

### 1. Presentation Layer

```
┌─────────────────────────────────────────────┐
│            JAZZMIN THEME                    │
├─────────────────────────────────────────────┤
│  ├─ Navigation Bar (Fixed Top)              │
│  │   └─ Home, Dashboard, Apps, User Menu    │
│  │                                           │
│  ├─ Sidebar (Collapsible)                   │
│  │   ├─ Users App                            │
│  │   │   ├─ Profiles                         │
│  │   │   └─ Bank Accounts                    │
│  │   │                                       │
│  │   ├─ Trading App                          │
│  │   │   ├─ Products                         │
│  │   │   ├─ Orders                           │
│  │   │   ├─ Transactions                     │
│  │   │   └─ Withdraw Requests                │
│  │   │                                       │
│  │   └─ Authentication                       │
│  │       ├─ Users                            │
│  │       └─ Groups                           │
│  │                                           │
│  └─ Main Content Area                        │
│      ├─ List Views (with filters)           │
│      ├─ Detail Views (with tabs)            │
│      └─ Dashboard (custom)                   │
└─────────────────────────────────────────────┘
```

### 2. Dashboard Architecture

```
┌──────────────────────────────────────────────────┐
│              CUSTOM DASHBOARD                     │
│        /admin/dashboard/                          │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │         KPI CARDS (Top Row)                │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐     │  │
│  │  │ Users   │ │ Orders  │ │ Txns    │ ... │  │
│  │  └─────────┘ └─────────┘ └─────────┘     │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │         ALERTS (If Any)                    │  │
│  │  ⚠️ Pending orders                         │  │
│  │  📥 Pending transactions                   │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │      DETAILED STATISTICS (Grid)            │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ User     │ │ Order    │ │ Txn      │  │  │
│  │  │ Stats    │ │ Stats    │ │ Stats    │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘  │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │      RECENT ACTIVITY (3 Columns)           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ Recent   │ │ Recent   │ │ New      │  │  │
│  │  │ Orders   │ │ Txns     │ │ Users    │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘  │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │      TOP USERS (By Order Value)            │  │
│  │  1. User A - 10M Rial                      │  │
│  │  2. User B - 8M Rial                       │  │
│  │  ...                                        │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 3. Enhanced Admin List View

```
┌──────────────────────────────────────────────────────┐
│                ORDER ADMIN LIST                       │
├──────────────────────────────────────────────────────┤
│  Actions: [Complete Orders] [Cancel Orders] [Go]     │
│  Export: [Excel] [CSV] [JSON]                        │
│  Import: [Choose File]                               │
├──────────────────────────────────────────────────────┤
│  Filters:                                            │
│    ├─ Status: [All] [Pending] [Completed]          │
│    ├─ Order Type: [All] [Buy] [Sell]               │
│    ├─ Product: [All] [Gold] [Coin] [Dollar]        │
│    ├─ Created: [Date Range Picker]                  │
│    └─ Amount: [Min: ___] [Max: ___]                │
├──────────────────────────────────────────────────────┤
│  Search: [User, Phone, Order ID...]                 │
├──────────────────────────────────────────────────────┤
│  ☑ | ID | User | Product | Type | Status | Amount  │
│  ☑ | 1  | Ali  | Gold    | 🟢   | 🟡     | 10M    │
│  ☑ | 2  | Sara | Coin    | 🔵   | 🟢     | 5M     │
│  ...                                                 │
└──────────────────────────────────────────────────────┘

Legend:
🟢 = Buy Order (Green Badge)
🔵 = Sell Order (Blue Badge)
🟡 = Pending Status (Yellow Badge)
🟢 = Completed Status (Green Badge)
```

### 4. Data Flow

```
┌─────────────┐
│   ADMIN     │
│   USER      │
└──────┬──────┘
       │
       │ 1. Action (Approve, Export, etc.)
       ▼
┌──────────────┐
│  DJANGO      │
│  ADMIN VIEW  │
└──────┬───────┘
       │
       │ 2. Process Request
       ▼
┌──────────────┐      ┌──────────────┐
│   MODEL      │◄────►│  DATABASE    │
│   MANAGER    │      │              │
└──────┬───────┘      └──────────────┘
       │
       │ 3. Return Data
       ▼
┌──────────────┐
│  TEMPLATE    │
│  RENDERING   │
└──────┬───────┘
       │
       │ 4. HTML Response
       ▼
┌──────────────┐
│   BROWSER    │
│   (Admin)    │
└──────────────┘
```

### 5. Import/Export Flow

```
IMPORT:
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Upload  │───►│ Validate │───►│  Parse   │───►│  Save    │
│  File   │    │  Format  │    │  Data    │    │  to DB   │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                     │                               │
                     ▼                               ▼
              ┌──────────┐                   ┌──────────┐
              │  Error   │                   │  Audit   │
              │  Report  │                   │  Log     │
              └──────────┘                   └──────────┘

EXPORT:
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Select  │───►│  Query   │───►│  Format  │───►│ Download │
│ Format  │    │   Data   │    │  Output  │    │   File   │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 6. Audit Logging Flow

```
┌─────────────┐
│ Admin       │
│ Action      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Auditlog        │
│ Middleware      │
│ - Capture user  │
│ - Capture time  │
│ - Capture action│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐      ┌─────────────────┐
│ Model Signal    │─────►│ Create Audit    │
│ (pre/post save) │      │ Log Entry       │
└─────────────────┘      └──────┬──────────┘
                                │
                                ▼
                         ┌─────────────────┐
                         │ LogEntry Model  │
                         │ - User          │
                         │ - Timestamp     │
                         │ - Changes       │
                         │ - Action        │
                         └─────────────────┘
```

---

## Technology Stack Layers

```
┌─────────────────────────────────────────────────────┐
│                  PRESENTATION                        │
│  - Jazzmin Theme (Bootstrap 4)                      │
│  - Custom CSS (Gradients, Badges)                   │
│  - Font Awesome Icons                               │
│  - jQuery (Interactions)                            │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│                  APPLICATION                         │
│  - Django Admin Framework                           │
│  - Custom Admin Classes                             │
│  - Custom Views (Dashboard)                         │
│  - Template Overrides                               │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC                     │
│  - Model Managers                                   │
│  - Service Layer                                    │
│  - Validation Logic                                 │
│  - Business Rules                                   │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│                   DATA ACCESS                        │
│  - Django ORM                                       │
│  - Model Definitions                                │
│  - Querysets                                        │
│  - Database Transactions                            │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│                    DATABASE                          │
│  - SQLite (Development)                             │
│  - PostgreSQL (Production)                          │
│  - Indexes                                          │
│  - Constraints                                      │
└─────────────────────────────────────────────────────┘
```

---

## Package Integration Map

```
┌──────────────────────────────────────────────────────┐
│                  DJANGO ADMIN                         │
└────────────────────┬─────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
│ Jazzmin   │  │ Import/ │  │  Audit    │
│  Theme    │  │ Export  │  │  Log      │
└─────┬─────┘  └────┬────┘  └─────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
│ Range     │  │ Admin   │  │  Django   │
│ Filter    │  │ Actions │  │  Filter   │
└───────────┘  └─────────┘  └───────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                  SECURITY LAYERS                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. AUTHENTICATION                                  │
│     ├─ Django Auth System                          │
│     ├─ Session Management                          │
│     └─ Password Hashing                            │
│                                                      │
│  2. AUTHORIZATION                                   │
│     ├─ Permission System                           │
│     ├─ Staff User Check                            │
│     └─ Superuser Check                             │
│                                                      │
│  3. DATA PROTECTION                                 │
│     ├─ Account Number Masking                      │
│     ├─ Sensitive Field Protection                  │
│     └─ HTTPS Enforcement (Production)              │
│                                                      │
│  4. AUDIT TRAIL                                     │
│     ├─ Action Logging                              │
│     ├─ User Tracking                               │
│     └─ Timestamp Recording                         │
│                                                      │
│  5. INPUT VALIDATION                                │
│     ├─ Form Validation                             │
│     ├─ Import Validation                           │
│     └─ Type Checking                               │
│                                                      │
│  6. TRANSACTION SAFETY                              │
│     ├─ Atomic Operations                           │
│     ├─ Database Constraints                        │
│     └─ Error Handling                              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
DEVELOPMENT:
┌────────────┐
│  Django    │
│  Dev Server│
│  :8000     │
└─────┬──────┘
      │
┌─────▼──────┐
│  SQLite    │
│  Database  │
└────────────┘

PRODUCTION:
┌────────────┐    ┌────────────┐
│   Nginx    │───►│  Gunicorn  │
│  :80/:443  │    │   Django   │
└────────────┘    └─────┬──────┘
                        │
                  ┌─────▼──────┐
                  │ PostgreSQL │
                  │  Database  │
                  └────────────┘
```

---

This architecture provides a **scalable, secure, and maintainable** foundation for the Gold Trading Bot admin panel! 🚀

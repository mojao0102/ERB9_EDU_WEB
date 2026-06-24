# NGO Course Management System

香港非牟利機構課程管理與報名平台。系統以 Django 建立，提供公開課程瀏覽、學生帳號與線上報名付款、職員後台、課程排期、交易記錄、收益分析、PDF 收據與報表等功能。

## 主要功能

- 公開網站：首頁、關於我們、消息公告、課程分類、課程列表與課程詳情
- 學生帳號：註冊、Email 驗證、登入、忘記密碼、修改個人資料與密碼
- 課程報名：Stripe Checkout 付款、Webhook 確認、付款成功與失敗處理
- 學生儀表板：課程狀態、報名歷史、付款/退款記錄、PDF 收據、個人課堂日曆
- 職員後台：後台登入、課程模板、課程管理、排期總覽、學生管理、導師管理、消息管理
- 交易與報表：交易篩選、CSV 匯出、PDF 報表、收益分析與熱門課程類別排行
- 文件輸出：付款收據、退款收據、交易報表 PDF
- 展示素材：`remotion-intro/` 內含 Remotion 影片與 HTML 簡報素材

## 技術棧

- Python / Django 5.2
- PostgreSQL
- Stripe API
- WeasyPrint PDF
- python-dotenv
- Hashids
- django-debug-toolbar
- django-widget-tweaks
- django-colorfield
- Remotion / React（簡報與影片展示用）

## 專案結構

```text
.
├── administration/      # 職員登入、後台 dashboard、交易、排期、報表
├── config/              # Django settings、urls、static assets
├── core/                # 共用 model、utils、hash id 工具
├── courses/             # 課程分類、模板、課程、排期、報名、退款、PDF 收據
├── front_web/           # 公開網站、學生帳號、付款、學生 dashboard、日曆
├── students/            # 後台學生管理
├── teachers/            # 後台導師管理
├── web_contents/        # 後台消息公告管理
├── remotion-intro/      # Remotion 影片與 HTML/PPT 展示檔
├── static/              # collectstatic 輸出目錄
├── manage.py
└── requirements.txt
```

## 系統需求

- Python 3.11 或以上
- PostgreSQL
- pip / virtualenv
- 可用的 SMTP 帳號（寄送驗證信與通知信）
- Stripe 帳號與 API keys

PDF 功能使用 WeasyPrint。macOS 如遇到 PDF 依賴問題，通常需要安裝相關系統套件，例如：

```bash
brew install pango
```

## 安裝與啟動

1. 建立並啟用虛擬環境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 安裝 Python 套件

```bash
pip install -r requirements.txt
```

3. 建立 `.env`

```env
SECRET_KEY=your-django-secret-key

DB_ENGINE='django.db.backends.postgresql'
DB_NAME=your_db_name
DB_LOGIN_ID=your_db_username
DB_PASSWORD=your_db_user_password
DB_HOST=your_db_host
DB_PORT=your_db_port

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password

STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_CURRENCY=hkd
STRIPE_API_VERSION=2026-05-27.dahlia

HASHIDS_SALT=your-hashids-salt
HASHIDS_MIN_LENGTH=8
```

請按本機 PostgreSQL 設定建立資料庫，或修改 `config/settings.py`。

4. 執行 migration

```bash
python manage.py migrate
```

5. 建立 Django admin 帳號

```bash
python manage.py createsuperuser
```

6. 啟動開發伺服器

```bash
python manage.py runserver
```

預設網址：

- 公開網站：http://127.0.0.1:8000/
- 職員後台：http://127.0.0.1:8000/manage/login/
- Django Admin：http://127.0.0.1:8000/admin/

## 常用路由

### 前台與學生端

| 功能 | 路由 |
| --- | --- |
| 首頁 | `/` |
| 關於我們 | `/about/` |
| 消息列表 | `/newses/` |
| 課程列表 | `/course_list/<hash_mc>/` |
| 課程詳情 | `/course/<hash_course>/` |
| 學生註冊 | `/register/` |
| 學生登入 | `/login/` |
| 課程付款 | `/course/<hash_course>/pay/` |
| 付款成功 | `/payment_successful/` |
| Stripe Webhook | `/stripe/webhook/` |
| 學生儀表板 | `/student_dashboard/` |
| 個人課堂日曆 | `/student/my-calendar/` |

### 職員後台

| 功能 | 路由 |
| --- | --- |
| 職員登入 | `/manage/login/` |
| 收益 dashboard | `/manage/dashboard` |
| 交易記錄 | `/manage/transactions/` |
| 排期總覽 | `/manage/schedules/` |
| 課程模板 | `/manage/courses/template/` |
| 課程管理 | `/manage/courses/list/` |
| 學生管理 | `/manage/students/list/` |
| 導師管理 | `/manage/teachers/list/` |
| 消息管理 | `/manage/web_contents/list/` |

## 主要資料模型

- `Staff`：後台職員帳號
- `Center` / `Room`：中心與課室
- `Student`：學生資料、登入帳號、Email 驗證狀態
- `Teacher`：導師資料
- `CourseMainCategory` / `CourseSubCategory`：課程分類
- `CourseTemplate`：可重用課程模板
- `Course`：實際開設課程
- `CourseSchedule`：課堂排期
- `SignUp`：課程報名與付款記錄
- `SignUpRefund`：退款記錄
- `News`：消息公告

## Stripe Webhook

本機開發可使用 Stripe CLI 轉發 webhook：

```bash
stripe listen --forward-to localhost:8000/stripe/webhook/
```

將 CLI 顯示的 `whsec_...` 填入 `.env`：

```env
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

## 靜態檔案與媒體檔案

開發環境會由 Django 處理 `MEDIA_URL`。正式環境部署時應另外設定靜態檔案與上傳檔案服務。

```bash
python manage.py collectstatic
```

相關設定：

- `STATIC_URL = "static/"`
- `STATIC_ROOT = BASE_DIR / "static"`
- `STATICFILES_DIRS = [BASE_DIR / "config/static"]`
- `MEDIA_URL = "/media/"`
- `MEDIA_ROOT = BASE_DIR / "media"`

## 測試與檢查

```bash
python manage.py check
python manage.py test
```


HTML 簡報位於：

```text
remotion-intro/PPT/ngo_system_ppt_Skill.html
remotion-intro/PPT/ngo_system_ppt_Skill_EN.html
```

## 開發注意事項

- 不要提交 `.env` 或任何真實 API key
- `DEBUG=True`、`ALLOWED_HOSTS=['*']` 只適合開發環境
- 正式環境應將資料庫密碼、Email 密碼、Stripe keys 移到環境變數
- 目前部分帳號密碼欄位以一般 `CharField` 儲存，正式上線前應評估改用 Django authentication 或安全雜湊機制
- Hashids 依賴 `HASHIDS_SALT`，更換 salt 會影響既有 hash URL 的解析
- PDF 輸出依賴 WeasyPrint，部署環境需要安裝對應系統套件


⚠️ 教育用途免責聲明 / Academic Disclaimer本專案純屬個人在【港專職業訓練學院/Python網站框架開發助理證書(erb9)】的學術作業研究，不包含任何商業營利、推廣或營收意圖。This project is for academic and educational purposes only as part of a school assignment. It contains no commercial intent or monetary purpose.專案中所引用的商業資料與商標，其版權皆歸原公司所有。本專案已對敏感資料進行模糊化/去識別化處理。All business data and trademarks cited belong to their respective owners. Sensitive data has been anonymized/modified.若有任何侵權疑慮，請立即聯繫移除：【mojao0102.fl@gmail.com】。If you have any copyright concerns, please contact me at [mojao0102.fl@gmail.com] for immediate removal.
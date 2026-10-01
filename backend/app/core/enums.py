"""Enumerated values from spec §6 — single source for DB CHECKs and API validation."""

LANGUAGES = ("en", "hi", "mr", "ta")
TRANSLATION_LANGUAGES = ("hi", "mr", "ta")

# users / profiles
ROLES = ("user", "admin")
USER_STATUSES = ("active", "deleted")
GENDERS = ("male", "female", "other", "prefer_not_to_say")
AREA_TYPES = ("rural", "urban")
OCCUPATION_TYPES = (
    "farmer", "student", "gig_worker", "senior_citizen", "small_business_owner", "salaried", "other",
)
INCOME_PATTERNS = ("fixed_monthly", "irregular", "seasonal")
SOCIAL_CATEGORIES = ("general", "obc", "sc", "st", "prefer_not_to_say")
CONFIDENCE_LEVELS = ("low", "medium", "high")
STATE_CODES = (
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DN", "DL", "GA", "GJ", "HR", "HP", "JK", "JH", "KA",
    "KL", "LA", "LD", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PY", "PB", "RJ", "SK", "TN", "TS",
    "TR", "UP", "UK", "WB",
)
CONSENT_TYPES = ("terms_privacy", "personalization", "push_notifications")
PLATFORMS = ("android", "ios")

# chat / memory
CHANNELS = ("app_text", "app_voice", "call")
MESSAGE_ROLES = ("user", "assistant")
INPUT_MODES = ("text", "voice")
MEMORY_CATEGORIES = ("preference", "fact", "goal_context", "concern", "behavior")

# finance
TRANSACTION_TYPES = ("income", "expense")
INCOME_CATEGORIES = (
    "crop_sale", "wages", "salary", "gig_payout", "allowance", "pension", "business", "other_income",
)
EXPENSE_CATEGORIES = (
    "food", "housing_rent", "utilities", "transport", "health", "education", "farm_inputs",
    "debt_repayment", "insurance_premium", "subscriptions", "entertainment", "other_expense",
)
ESSENTIAL_CATEGORIES = (
    "food", "housing_rent", "utilities", "transport", "health", "education", "farm_inputs",
    "debt_repayment", "insurance_premium",
)
TRANSACTION_SOURCES = ("manual", "voice", "chat")
DEBT_TYPES = (
    "bank_loan", "kisan_credit_card", "credit_card", "microfinance", "moneylender", "family_friend", "other",
)
DEBT_STATUSES = ("active", "closed")

# goals / planner
GOAL_CATEGORIES = (
    "emergency_fund", "education", "vehicle", "home", "wedding", "medical", "retirement", "business",
    "farm_equipment", "custom",
)
GOAL_STATUSES = ("active", "completed", "paused", "cancelled")
BUDGET_MODES = ("lean", "normal", "surplus")
FORECAST_CONFIDENCE = ("low", "medium", "high")
RISK_LEVELS = ("low", "medium", "high")

# insights / notifications
INSIGHT_TYPES = ("spending", "savings", "goal", "income", "emergency_fund", "scheme", "risk")
INSIGHT_TONES = ("info", "warning", "positive")
INSIGHT_FILTER_GROUPS = ("savings", "spending", "goals", "other")
NOTIFICATION_STATUSES = ("queued", "sent", "failed", "skipped")

# schemes
SCHEME_LEVELS = ("central", "state")
BENEFIT_TYPES = (
    "cash", "insurance", "loan", "subsidy", "pension", "scholarship", "employment", "health_cover",
    "housing", "savings",
)
RULE_OPERATORS = ("eq", "neq", "in", "not_in", "gte", "lte", "between", "is_true", "is_false")
GENERATED_BY = ("llm", "human")
MATCH_STATUSES = ("eligible", "possibly_eligible", "not_eligible")
TRACKING_STATUSES = ("saved", "applied", "dismissed")

# fraud
FRAUD_PATTERN_TYPES = ("regex", "keyword", "url", "negative")
FRAUD_INPUT_TYPES = ("text", "screenshot", "shared_text")
SOURCE_APPS = ("whatsapp", "sms", "other")
VERDICTS = ("safe", "suspicious", "dangerous")

# learn
GLOSSARY_CATEGORIES = ("basics", "investing", "savings", "insurance", "loans")
LESSON_CATEGORIES = ("basics", "investing", "savings", "insurance")
DIFFICULTIES = ("easy", "medium")

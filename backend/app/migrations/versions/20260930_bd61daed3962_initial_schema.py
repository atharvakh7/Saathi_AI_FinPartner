"""initial schema — all tables from spec §6 (extensions pgcrypto, vector)

Revision ID: bd61daed3962
Revises: 
Create Date: 2026-09-30 19:54:16.942177+00:00
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = 'bd61daed3962'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # gen_random_uuid() needs pgcrypto on older servers; vector provides the pgvector type.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('fraud_patterns',
    sa.Column('code', sa.String(length=8), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('pattern_type', sa.String(length=10), nullable=False),
    sa.Column('patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('weight', sa.SmallInteger(), nullable=False),
    sa.Column('requires_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('reason_key', sa.String(length=40), nullable=True),
    sa.Column('reason_title_en', sa.String(length=80), nullable=True),
    sa.Column('reason_text_en', sa.String(length=200), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("pattern_type IN ('regex', 'keyword', 'url', 'negative')", name=op.f('ck_fraud_patterns_pattern_type_valid')),
    sa.CheckConstraint('weight >= -100 AND weight <= 100', name=op.f('ck_fraud_patterns_weight_range')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fraud_patterns')),
    sa.UniqueConstraint('code', name=op.f('uq_fraud_patterns_code'))
    )
    op.create_table('goal_templates',
    sa.Column('slug', sa.String(length=20), nullable=False),
    sa.Column('title_en', sa.String(length=80), nullable=False),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.SmallInteger(), nullable=False),
    sa.Column('default_target_inr', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.CheckConstraint("category IN ('emergency_fund', 'education', 'vehicle', 'home', 'wedding', 'medical', 'retirement', 'business', 'farm_equipment', 'custom')", name=op.f('ck_goal_templates_category_valid')),
    sa.PrimaryKeyConstraint('slug', name=op.f('pk_goal_templates'))
    )
    op.create_table('otp_requests',
    sa.Column('phone_e164', sa.String(length=16), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('attempts', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('request_ip', postgresql.INET(), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_otp_requests'))
    )
    op.create_index('ix_otp_requests_phone_created', 'otp_requests', ['phone_e164', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('scheme_categories',
    sa.Column('slug', sa.String(length=30), nullable=False),
    sa.Column('name_en', sa.String(length=60), nullable=False),
    sa.Column('icon', sa.String(length=30), nullable=False),
    sa.Column('sort_order', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('slug', name=op.f('pk_scheme_categories'))
    )
    op.create_table('users',
    sa.Column('phone_e164', sa.String(length=16), nullable=False),
    sa.Column('role', sa.String(length=10), server_default='user', nullable=False),
    sa.Column('preferred_language', sa.String(length=2), server_default='en', nullable=False),
    sa.Column('status', sa.String(length=10), server_default='active', nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("phone_e164 ~ '^\\+91[6-9][0-9]{9}$'", name=op.f('ck_users_phone_e164_format')),
    sa.CheckConstraint("preferred_language IN ('en', 'hi', 'mr', 'ta')", name=op.f('ck_users_preferred_language_valid')),
    sa.CheckConstraint("role IN ('user', 'admin')", name=op.f('ck_users_role_valid')),
    sa.CheckConstraint("status IN ('active', 'deleted')", name=op.f('ck_users_status_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('phone_e164', name=op.f('uq_users_phone_e164'))
    )
    op.create_table('videos',
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('storage_key', sa.String(length=200), nullable=False),
    sa.Column('thumbnail_key', sa.String(length=200), nullable=True),
    sa.Column('duration_sec', sa.Integer(), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("language IN ('en', 'hi', 'mr', 'ta')", name=op.f('ck_videos_language_valid')),
    sa.CheckConstraint('duration_sec >= 0', name=op.f('ck_videos_duration_sec_range')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_videos'))
    )
    op.create_table('budgets',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('month', sa.Date(), nullable=False),
    sa.Column('mode', sa.String(length=8), nullable=False),
    sa.Column('expected_income_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('planning_income_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('needs_limit_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('wants_limit_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('savings_target_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('generation_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("mode IN ('lean', 'normal', 'surplus')", name=op.f('ck_budgets_mode_valid')),
    sa.CheckConstraint('EXTRACT(DAY FROM month) = 1', name=op.f('ck_budgets_month_first_day')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_budgets_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_budgets')),
    sa.UniqueConstraint('user_id', 'month', name=op.f('uq_budgets_user_id_month'))
    )
    op.create_table('cashflow_forecasts',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('month', sa.Date(), nullable=False),
    sa.Column('expected_income_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('lower_income_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('upper_income_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('expected_expense_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('expected_net_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('mode', sa.String(length=8), nullable=False),
    sa.Column('confidence', sa.String(length=6), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("confidence IN ('low', 'medium', 'high')", name=op.f('ck_cashflow_forecasts_confidence_valid')),
    sa.CheckConstraint("mode IN ('lean', 'normal', 'surplus')", name=op.f('ck_cashflow_forecasts_mode_valid')),
    sa.CheckConstraint('EXTRACT(DAY FROM month) = 1', name=op.f('ck_cashflow_forecasts_month_first_day')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_cashflow_forecasts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cashflow_forecasts')),
    sa.UniqueConstraint('user_id', 'month', name=op.f('uq_cashflow_forecasts_user_id_month'))
    )
    op.create_table('consents',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('consent_type', sa.String(length=30), nullable=False),
    sa.Column('version', sa.String(length=10), nullable=False),
    sa.Column('granted', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("consent_type IN ('terms_privacy', 'personalization', 'push_notifications')", name=op.f('ck_consents_consent_type_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_consents_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consents'))
    )
    op.create_index('ix_consents_user_type_created', 'consents', ['user_id', 'consent_type', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('conversations',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('channel', sa.String(length=12), nullable=False),
    sa.Column('title', sa.String(length=80), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('summary_updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_message_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_archived', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("channel IN ('app_text', 'app_voice', 'call')", name=op.f('ck_conversations_channel_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_conversations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conversations'))
    )
    op.create_index('ix_conversations_user_last_message', 'conversations', ['user_id', sa.literal_column('last_message_at DESC')], unique=False)
    op.create_table('debts',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('lender_name', sa.String(length=80), nullable=False),
    sa.Column('debt_type', sa.String(length=20), nullable=False),
    sa.Column('principal_outstanding_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('interest_rate_pct', sa.Numeric(precision=5, scale=2), server_default=sa.text('0'), nullable=False),
    sa.Column('min_monthly_payment_inr', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=False),
    sa.Column('due_day_of_month', sa.SmallInteger(), nullable=True),
    sa.Column('status', sa.String(length=8), server_default='active', nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("debt_type IN ('bank_loan', 'kisan_credit_card', 'credit_card', 'microfinance', 'moneylender', 'family_friend', 'other')", name=op.f('ck_debts_debt_type_valid')),
    sa.CheckConstraint("status IN ('active', 'closed')", name=op.f('ck_debts_status_valid')),
    sa.CheckConstraint('due_day_of_month >= 1 AND due_day_of_month <= 31', name=op.f('ck_debts_due_day_of_month_range')),
    sa.CheckConstraint('interest_rate_pct >= 0 AND interest_rate_pct <= 120', name=op.f('ck_debts_interest_rate_pct_range')),
    sa.CheckConstraint('min_monthly_payment_inr >= 0', name=op.f('ck_debts_min_monthly_payment_inr_range')),
    sa.CheckConstraint('principal_outstanding_inr >= 0', name=op.f('ck_debts_principal_outstanding_inr_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_debts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_debts'))
    )
    op.create_index('ix_debts_user_status', 'debts', ['user_id', 'status'], unique=False)
    op.create_table('device_tokens',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('expo_push_token', sa.String(length=200), nullable=False),
    sa.Column('platform', sa.String(length=10), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("platform IN ('android', 'ios')", name=op.f('ck_device_tokens_platform_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_device_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_device_tokens')),
    sa.UniqueConstraint('expo_push_token', name=op.f('uq_device_tokens_expo_push_token'))
    )
    op.create_index(op.f('ix_device_tokens_user_id'), 'device_tokens', ['user_id'], unique=False)
    op.create_table('fraud_checks',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('input_type', sa.String(length=12), nullable=False),
    sa.Column('source_app', sa.String(length=10), server_default='other', nullable=False),
    sa.Column('extracted_text', sa.Text(), nullable=False),
    sa.Column('text_hash', sa.String(length=64), nullable=False),
    sa.Column('snippet', sa.String(length=60), nullable=False),
    sa.Column('risk_score', sa.SmallInteger(), nullable=False),
    sa.Column('verdict', sa.String(length=10), nullable=False),
    sa.Column('matched_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('classifier_score', sa.Numeric(precision=4, scale=3), nullable=True),
    sa.Column('explanation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('extracted_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("input_type IN ('text', 'screenshot', 'shared_text')", name=op.f('ck_fraud_checks_input_type_valid')),
    sa.CheckConstraint("language IN ('en', 'hi', 'mr', 'ta')", name=op.f('ck_fraud_checks_language_valid')),
    sa.CheckConstraint("source_app IN ('whatsapp', 'sms', 'other')", name=op.f('ck_fraud_checks_source_app_valid')),
    sa.CheckConstraint("verdict IN ('safe', 'suspicious', 'dangerous')", name=op.f('ck_fraud_checks_verdict_valid')),
    sa.CheckConstraint('classifier_score >= 0 AND classifier_score <= 1', name=op.f('ck_fraud_checks_classifier_score_range')),
    sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name=op.f('ck_fraud_checks_risk_score_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_fraud_checks_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fraud_checks'))
    )
    op.create_index(op.f('ix_fraud_checks_text_hash'), 'fraud_checks', ['text_hash'], unique=False)
    op.create_index('ix_fraud_checks_user_created', 'fraud_checks', ['user_id', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('glossary_terms',
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('term_en', sa.String(length=80), nullable=False),
    sa.Column('aliases', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('category', sa.String(length=10), nullable=False),
    sa.Column('definition_en', sa.String(length=400), nullable=False),
    sa.Column('example_en', sa.String(length=400), nullable=False),
    sa.Column('analogy_en', sa.String(length=300), nullable=False),
    sa.Column('key_takeaway_en', sa.String(length=150), nullable=False),
    sa.Column('related_slugs', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('video_id', sa.Uuid(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("category IN ('basics', 'investing', 'savings', 'insurance', 'loans')", name=op.f('ck_glossary_terms_category_valid')),
    sa.ForeignKeyConstraint(['video_id'], ['videos.id'], name=op.f('fk_glossary_terms_video_id_videos'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_glossary_terms')),
    sa.UniqueConstraint('slug', name=op.f('uq_glossary_terms_slug'))
    )
    op.create_table('goals',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=80), nullable=False),
    sa.Column('category', sa.String(length=20), nullable=False),
    sa.Column('target_amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('current_amount_inr', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=False),
    sa.Column('target_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=10), server_default='active', nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("category IN ('emergency_fund', 'education', 'vehicle', 'home', 'wedding', 'medical', 'retirement', 'business', 'farm_equipment', 'custom')", name=op.f('ck_goals_category_valid')),
    sa.CheckConstraint("status IN ('active', 'completed', 'paused', 'cancelled')", name=op.f('ck_goals_status_valid')),
    sa.CheckConstraint('current_amount_inr >= 0', name=op.f('ck_goals_current_amount_inr_range')),
    sa.CheckConstraint('target_amount_inr > 0', name=op.f('ck_goals_target_amount_inr_positive')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_goals_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_goals'))
    )
    op.create_index('ix_goals_user_status', 'goals', ['user_id', 'status'], unique=False)
    op.create_index('uq_goals_one_emergency_fund', 'goals', ['user_id'], unique=True, postgresql_where=sa.text("category = 'emergency_fund' AND status IN ('active', 'paused')"))
    op.create_table('insights',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('code', sa.String(length=4), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('tone', sa.String(length=10), nullable=False),
    sa.Column('filter_group', sa.String(length=10), nullable=False),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('body', sa.String(length=400), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('cta_route', sa.String(length=100), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('dedupe_key', sa.String(length=80), nullable=False),
    sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("filter_group IN ('savings', 'spending', 'goals', 'other')", name=op.f('ck_insights_filter_group_valid')),
    sa.CheckConstraint("language IN ('en', 'hi', 'mr', 'ta')", name=op.f('ck_insights_language_valid')),
    sa.CheckConstraint("tone IN ('info', 'warning', 'positive')", name=op.f('ck_insights_tone_valid')),
    sa.CheckConstraint("type IN ('spending', 'savings', 'goal', 'income', 'emergency_fund', 'scheme', 'risk')", name=op.f('ck_insights_type_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_insights_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_insights')),
    sa.UniqueConstraint('user_id', 'dedupe_key', name=op.f('uq_insights_user_id_dedupe_key'))
    )
    op.create_index('ix_insights_user_read_created', 'insights', ['user_id', 'is_read', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('lessons',
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('category', sa.String(length=10), nullable=False),
    sa.Column('sort_order', sa.SmallInteger(), nullable=False),
    sa.Column('title_en', sa.String(length=120), nullable=False),
    sa.Column('duration_min', sa.SmallInteger(), nullable=False),
    sa.Column('difficulty', sa.String(length=6), nullable=False),
    sa.Column('body_md_en', sa.Text(), nullable=False),
    sa.Column('video_id', sa.Uuid(), nullable=True),
    sa.Column('xp_reward', sa.SmallInteger(), server_default=sa.text('50'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("category IN ('basics', 'investing', 'savings', 'insurance')", name=op.f('ck_lessons_category_valid')),
    sa.CheckConstraint("difficulty IN ('easy', 'medium')", name=op.f('ck_lessons_difficulty_valid')),
    sa.CheckConstraint('duration_min >= 1', name=op.f('ck_lessons_duration_min_range')),
    sa.CheckConstraint('xp_reward >= 0', name=op.f('ck_lessons_xp_reward_range')),
    sa.ForeignKeyConstraint(['video_id'], ['videos.id'], name=op.f('fk_lessons_video_id_videos'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lessons')),
    sa.UniqueConstraint('slug', name=op.f('uq_lessons_slug'))
    )
    op.create_table('notification_settings',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('push_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('daily_insight_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('daily_insight_time', sa.Time(), server_default=sa.text("'09:00'"), nullable=False),
    sa.Column('income_reminder_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('goal_reminder_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('scheme_deadline_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('lean_month_alert_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('streak_reminder_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('streak_reminder_time', sa.Time(), server_default=sa.text("'20:00'"), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notification_settings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_notification_settings'))
    )
    op.create_table('notifications',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('body', sa.String(length=300), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=10), server_default='queued', nullable=False),
    sa.Column('scheduled_for', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('queued', 'sent', 'failed', 'skipped')", name=op.f('ck_notifications_status_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
    )
    op.create_index('ix_notifications_status_scheduled', 'notifications', ['status', 'scheduled_for'], unique=False)
    op.create_index('ix_notifications_user_created', 'notifications', ['user_id', sa.literal_column('created_at DESC')], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('device_id', sa.String(length=100), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('replaced_by', sa.Uuid(), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_tokens_token_hash'))
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_table('risk_snapshots',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('computed_on', sa.Date(), nullable=False),
    sa.Column('score', sa.Numeric(precision=2, scale=1), nullable=False),
    sa.Column('level', sa.String(length=6), nullable=False),
    sa.Column('components', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("level IN ('low', 'medium', 'high')", name=op.f('ck_risk_snapshots_level_valid')),
    sa.CheckConstraint('score >= 0 AND score <= 5', name=op.f('ck_risk_snapshots_score_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_risk_snapshots_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_risk_snapshots')),
    sa.UniqueConstraint('user_id', 'computed_on', name=op.f('uq_risk_snapshots_user_id_computed_on'))
    )
    op.create_table('schemes',
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('name_en', sa.String(length=150), nullable=False),
    sa.Column('level', sa.String(length=7), nullable=False),
    sa.Column('state_code', sa.String(length=2), nullable=True),
    sa.Column('category_slug', sa.String(length=30), nullable=False),
    sa.Column('ministry_or_dept', sa.String(length=120), nullable=True),
    sa.Column('benefit_type', sa.String(length=15), nullable=False),
    sa.Column('benefit_summary_en', sa.String(length=300), nullable=False),
    sa.Column('description_en', sa.Text(), nullable=False),
    sa.Column('application_mode_en', sa.String(length=200), nullable=True),
    sa.Column('official_url', sa.String(length=300), nullable=False),
    sa.Column('source_url', sa.String(length=300), nullable=False),
    sa.Column('last_verified_on', sa.Date(), nullable=False),
    sa.Column('deadline_on', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("benefit_type IN ('cash', 'insurance', 'loan', 'subsidy', 'pension', 'scholarship', 'employment', 'health_cover', 'housing', 'savings')", name=op.f('ck_schemes_benefit_type_valid')),
    sa.CheckConstraint("level = 'central' OR state_code IS NOT NULL", name=op.f('ck_schemes_state_scheme_has_state')),
    sa.CheckConstraint("level IN ('central', 'state')", name=op.f('ck_schemes_level_valid')),
    sa.CheckConstraint("state_code IN ('AN', 'AP', 'AR', 'AS', 'BR', 'CH', 'CG', 'DN', 'DL', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA', 'KL', 'LA', 'LD', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PY', 'PB', 'RJ', 'SK', 'TN', 'TS', 'TR', 'UP', 'UK', 'WB')", name=op.f('ck_schemes_state_code_valid')),
    sa.ForeignKeyConstraint(['category_slug'], ['scheme_categories.slug'], name=op.f('fk_schemes_category_slug_scheme_categories')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_schemes')),
    sa.UniqueConstraint('slug', name=op.f('uq_schemes_slug'))
    )
    op.create_index(op.f('ix_schemes_category_slug'), 'schemes', ['category_slug'], unique=False)
    op.create_index('ix_schemes_level_state', 'schemes', ['level', 'state_code'], unique=False)
    op.create_table('transactions',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('type', sa.String(length=7), nullable=False),
    sa.Column('amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('category', sa.String(length=25), nullable=False),
    sa.Column('is_essential', sa.Boolean(), nullable=False),
    sa.Column('occurred_on', sa.Date(), nullable=False),
    sa.Column('note', sa.String(length=200), nullable=True),
    sa.Column('source', sa.String(length=8), server_default='manual', nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("(type = 'income' AND category IN ('crop_sale', 'wages', 'salary', 'gig_payout', 'allowance', 'pension', 'business', 'other_income')) OR (type = 'expense' AND category IN ('food', 'housing_rent', 'utilities', 'transport', 'health', 'education', 'farm_inputs', 'debt_repayment', 'insurance_premium', 'subscriptions', 'entertainment', 'other_expense'))", name=op.f('ck_transactions_category_matches_type')),
    sa.CheckConstraint("source IN ('manual', 'voice', 'chat')", name=op.f('ck_transactions_source_valid')),
    sa.CheckConstraint("type = 'expense' OR is_essential = false", name=op.f('ck_transactions_income_not_essential')),
    sa.CheckConstraint("type IN ('income', 'expense')", name=op.f('ck_transactions_type_valid')),
    sa.CheckConstraint('amount_inr > 0', name=op.f('ck_transactions_amount_inr_positive')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_transactions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_transactions'))
    )
    op.create_index('ix_transactions_user_occurred', 'transactions', ['user_id', sa.literal_column('occurred_on DESC')], unique=False)
    op.create_index('ix_transactions_user_type_occurred', 'transactions', ['user_id', 'type', 'occurred_on'], unique=False)
    op.create_table('user_learning_stats',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('xp', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('level', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('streak_days', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('longest_streak', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('last_active_on', sa.Date(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('level >= 1', name=op.f('ck_user_learning_stats_level_range')),
    sa.CheckConstraint('longest_streak >= 0', name=op.f('ck_user_learning_stats_longest_streak_range')),
    sa.CheckConstraint('streak_days >= 0', name=op.f('ck_user_learning_stats_streak_days_range')),
    sa.CheckConstraint('xp >= 0', name=op.f('ck_user_learning_stats_xp_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_learning_stats_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_user_learning_stats'))
    )
    op.create_table('user_profiles',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('full_name', sa.String(length=80), nullable=True),
    sa.Column('age_years', sa.SmallInteger(), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('state_code', sa.String(length=2), nullable=True),
    sa.Column('district', sa.String(length=60), nullable=True),
    sa.Column('area_type', sa.String(length=10), nullable=True),
    sa.Column('occupation_type', sa.String(length=25), nullable=True),
    sa.Column('income_pattern', sa.String(length=15), nullable=True),
    sa.Column('declared_monthly_income_min_inr', sa.Integer(), nullable=True),
    sa.Column('declared_monthly_income_max_inr', sa.Integer(), nullable=True),
    sa.Column('household_size', sa.SmallInteger(), nullable=True),
    sa.Column('dependents_count', sa.SmallInteger(), nullable=True),
    sa.Column('annual_household_income_inr', sa.Integer(), nullable=True),
    sa.Column('land_holding_hectares', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('social_category', sa.String(length=20), nullable=True),
    sa.Column('has_bank_account', sa.Boolean(), nullable=True),
    sa.Column('is_land_owner', sa.Boolean(), nullable=True),
    sa.Column('is_bpl_household', sa.Boolean(), nullable=True),
    sa.Column('is_income_tax_payer', sa.Boolean(), nullable=True),
    sa.Column('is_student', sa.Boolean(), nullable=True),
    sa.Column('is_street_vendor', sa.Boolean(), nullable=True),
    sa.Column('is_unorganised_worker', sa.Boolean(), nullable=True),
    sa.Column('is_traditional_artisan', sa.Boolean(), nullable=True),
    sa.Column('has_pucca_house', sa.Boolean(), nullable=True),
    sa.Column('has_girl_child_below_10', sa.Boolean(), nullable=True),
    sa.Column('is_head_of_household', sa.Boolean(), nullable=True),
    sa.Column('is_govt_employee', sa.Boolean(), nullable=True),
    sa.Column('confidence_answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confidence_score_pct', sa.SmallInteger(), nullable=True),
    sa.Column('confidence_level', sa.String(length=10), nullable=True),
    sa.Column('voice_reply_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("area_type IN ('rural', 'urban')", name=op.f('ck_user_profiles_area_type_valid')),
    sa.CheckConstraint("confidence_level IN ('low', 'medium', 'high')", name=op.f('ck_user_profiles_confidence_level_valid')),
    sa.CheckConstraint("gender IN ('male', 'female', 'other', 'prefer_not_to_say')", name=op.f('ck_user_profiles_gender_valid')),
    sa.CheckConstraint("income_pattern IN ('fixed_monthly', 'irregular', 'seasonal')", name=op.f('ck_user_profiles_income_pattern_valid')),
    sa.CheckConstraint("occupation_type IN ('farmer', 'student', 'gig_worker', 'senior_citizen', 'small_business_owner', 'salaried', 'other')", name=op.f('ck_user_profiles_occupation_type_valid')),
    sa.CheckConstraint("social_category IN ('general', 'obc', 'sc', 'st', 'prefer_not_to_say')", name=op.f('ck_user_profiles_social_category_valid')),
    sa.CheckConstraint("state_code IN ('AN', 'AP', 'AR', 'AS', 'BR', 'CH', 'CG', 'DN', 'DL', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA', 'KL', 'LA', 'LD', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PY', 'PB', 'RJ', 'SK', 'TN', 'TS', 'TR', 'UP', 'UK', 'WB')", name=op.f('ck_user_profiles_state_code_valid')),
    sa.CheckConstraint('age_years >= 18 AND age_years <= 100', name=op.f('ck_user_profiles_age_years_range')),
    sa.CheckConstraint('annual_household_income_inr >= 0', name=op.f('ck_user_profiles_annual_household_income_inr_range')),
    sa.CheckConstraint('confidence_score_pct >= 0 AND confidence_score_pct <= 100', name=op.f('ck_user_profiles_confidence_score_pct_range')),
    sa.CheckConstraint('declared_monthly_income_max_inr >= 0 AND (declared_monthly_income_min_inr IS NULL OR declared_monthly_income_max_inr >= declared_monthly_income_min_inr)', name=op.f('ck_user_profiles_declared_monthly_income_max_inr_range')),
    sa.CheckConstraint('declared_monthly_income_min_inr >= 0', name=op.f('ck_user_profiles_declared_monthly_income_min_inr_range')),
    sa.CheckConstraint('dependents_count >= 0 AND dependents_count <= 19', name=op.f('ck_user_profiles_dependents_count_range')),
    sa.CheckConstraint('household_size >= 1 AND household_size <= 20', name=op.f('ck_user_profiles_household_size_range')),
    sa.CheckConstraint('land_holding_hectares >= 0 AND land_holding_hectares <= 500', name=op.f('ck_user_profiles_land_holding_hectares_range')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_profiles_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_user_profiles'))
    )
    op.create_table('emergency_fund_plans',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('goal_id', sa.Uuid(), nullable=False),
    sa.Column('target_months', sa.SmallInteger(), nullable=False),
    sa.Column('monthly_essential_expense_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('target_amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('suggested_monthly_contribution_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('started_on', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('target_months >= 1 AND target_months <= 12', name=op.f('ck_emergency_fund_plans_target_months_range')),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name=op.f('fk_emergency_fund_plans_goal_id_goals')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_emergency_fund_plans_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_emergency_fund_plans')),
    sa.UniqueConstraint('goal_id', name=op.f('uq_emergency_fund_plans_goal_id')),
    sa.UniqueConstraint('user_id', name=op.f('uq_emergency_fund_plans_user_id'))
    )
    op.create_table('fraud_reports',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('fraud_check_id', sa.Uuid(), nullable=True),
    sa.Column('text_hash', sa.String(length=64), nullable=False),
    sa.Column('matched_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('extracted_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['fraud_check_id'], ['fraud_checks.id'], name=op.f('fk_fraud_reports_fraud_check_id_fraud_checks'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_fraud_reports_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fraud_reports')),
    sa.UniqueConstraint('user_id', 'text_hash', name=op.f('uq_fraud_reports_user_id_text_hash'))
    )
    op.create_index(op.f('ix_fraud_reports_text_hash'), 'fraud_reports', ['text_hash'], unique=False)
    op.create_table('glossary_translations',
    sa.Column('term_id', sa.Uuid(), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('term_local', sa.String(length=120), nullable=False),
    sa.Column('definition', sa.String(length=600), nullable=False),
    sa.Column('example', sa.String(length=600), nullable=False),
    sa.Column('analogy', sa.String(length=500), nullable=False),
    sa.Column('key_takeaway', sa.String(length=250), nullable=False),
    sa.Column('generated_by', sa.String(length=5), nullable=False),
    sa.Column('reviewed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("generated_by IN ('llm', 'human')", name=op.f('ck_glossary_translations_generated_by_valid')),
    sa.CheckConstraint("language IN ('hi', 'mr', 'ta')", name=op.f('ck_glossary_translations_language_valid')),
    sa.ForeignKeyConstraint(['term_id'], ['glossary_terms.id'], name=op.f('fk_glossary_translations_term_id_glossary_terms'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_glossary_translations')),
    sa.UniqueConstraint('term_id', 'language', name=op.f('uq_glossary_translations_term_id_language'))
    )
    op.create_table('goal_contributions',
    sa.Column('goal_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('amount_inr', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('contributed_on', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
    sa.Column('note', sa.String(length=200), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('amount_inr <> 0', name=op.f('ck_goal_contributions_amount_inr_nonzero')),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name=op.f('fk_goal_contributions_goal_id_goals'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_goal_contributions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_goal_contributions'))
    )
    op.create_index('ix_goal_contributions_goal_date', 'goal_contributions', ['goal_id', sa.literal_column('contributed_on DESC')], unique=False)
    op.create_table('lesson_progress',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('lesson_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.String(length=9), server_default='completed', nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("status IN ('completed')", name=op.f('ck_lesson_progress_status_valid')),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_lesson_progress_lesson_id_lessons'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_lesson_progress_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lesson_progress')),
    sa.UniqueConstraint('user_id', 'lesson_id', name=op.f('uq_lesson_progress_user_id_lesson_id'))
    )
    op.create_table('lesson_translations',
    sa.Column('lesson_id', sa.Uuid(), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('body_md', sa.Text(), nullable=False),
    sa.Column('generated_by', sa.String(length=5), nullable=False),
    sa.Column('reviewed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("generated_by IN ('llm', 'human')", name=op.f('ck_lesson_translations_generated_by_valid')),
    sa.CheckConstraint("language IN ('hi', 'mr', 'ta')", name=op.f('ck_lesson_translations_language_valid')),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_lesson_translations_lesson_id_lessons'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lesson_translations')),
    sa.UniqueConstraint('lesson_id', 'language', name=op.f('uq_lesson_translations_lesson_id_language'))
    )
    op.create_table('messages',
    sa.Column('conversation_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=True),
    sa.Column('input_mode', sa.String(length=6), server_default='text', nullable=False),
    sa.Column('intent', sa.String(length=20), nullable=True),
    sa.Column('tool_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('cards', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('highlighted_terms', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('suggested_replies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tokens_in', sa.Integer(), nullable=True),
    sa.Column('tokens_out', sa.Integer(), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("input_mode IN ('text', 'voice')", name=op.f('ck_messages_input_mode_valid')),
    sa.CheckConstraint("language IN ('en', 'hi', 'mr', 'ta')", name=op.f('ck_messages_language_valid')),
    sa.CheckConstraint("role IN ('user', 'assistant')", name=op.f('ck_messages_role_valid')),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_messages_conversation_id_conversations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_messages_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'], unique=False)
    op.create_table('scheme_documents',
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('document_name_en', sa.String(length=120), nullable=False),
    sa.Column('is_mandatory', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('sort_order', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_scheme_documents_scheme_id_schemes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scheme_documents'))
    )
    op.create_index(op.f('ix_scheme_documents_scheme_id'), 'scheme_documents', ['scheme_id'], unique=False)
    op.create_table('scheme_eligibility_rules',
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('rule_key', sa.String(length=60), nullable=False),
    sa.Column('field', sa.String(length=50), nullable=False),
    sa.Column('operator', sa.String(length=10), nullable=False),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_mandatory', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('explanation_en', sa.String(length=200), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("operator IN ('eq', 'neq', 'in', 'not_in', 'gte', 'lte', 'between', 'is_true', 'is_false')", name=op.f('ck_scheme_eligibility_rules_operator_valid')),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_scheme_eligibility_rules_scheme_id_schemes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scheme_eligibility_rules')),
    sa.UniqueConstraint('scheme_id', 'rule_key', name=op.f('uq_scheme_eligibility_rules_scheme_id_rule_key'))
    )
    op.create_table('scheme_steps',
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('step_no', sa.SmallInteger(), nullable=False),
    sa.Column('title_en', sa.String(length=100), nullable=False),
    sa.Column('description_en', sa.String(length=400), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_scheme_steps_scheme_id_schemes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scheme_steps')),
    sa.UniqueConstraint('scheme_id', 'step_no', name=op.f('uq_scheme_steps_scheme_id_step_no'))
    )
    op.create_table('scheme_translations',
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('generated_by', sa.String(length=5), nullable=False),
    sa.Column('reviewed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("generated_by IN ('llm', 'human')", name=op.f('ck_scheme_translations_generated_by_valid')),
    sa.CheckConstraint("language IN ('hi', 'mr', 'ta')", name=op.f('ck_scheme_translations_language_valid')),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_scheme_translations_scheme_id_schemes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scheme_translations')),
    sa.UniqueConstraint('scheme_id', 'language', name=op.f('uq_scheme_translations_scheme_id_language'))
    )
    op.create_table('term_feedback',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('term_id', sa.Uuid(), nullable=False),
    sa.Column('helpful', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['term_id'], ['glossary_terms.id'], name=op.f('fk_term_feedback_term_id_glossary_terms'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_term_feedback_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_term_feedback')),
    sa.UniqueConstraint('user_id', 'term_id', name=op.f('uq_term_feedback_user_id_term_id'))
    )
    op.create_table('user_scheme_matches',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.String(length=17), nullable=False),
    sa.Column('rule_results', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.CheckConstraint("status IN ('eligible', 'possibly_eligible', 'not_eligible')", name=op.f('ck_user_scheme_matches_status_valid')),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_user_scheme_matches_scheme_id_schemes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_scheme_matches_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_scheme_matches')),
    sa.UniqueConstraint('user_id', 'scheme_id', name=op.f('uq_user_scheme_matches_user_id_scheme_id'))
    )
    op.create_index('ix_user_scheme_matches_user_status', 'user_scheme_matches', ['user_id', 'status'], unique=False)
    op.create_table('user_scheme_tracking',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('scheme_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("status IN ('saved', 'applied', 'dismissed')", name=op.f('ck_user_scheme_tracking_status_valid')),
    sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], name=op.f('fk_user_scheme_tracking_scheme_id_schemes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_scheme_tracking_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_scheme_tracking')),
    sa.UniqueConstraint('user_id', 'scheme_id', name=op.f('uq_user_scheme_tracking_user_id_scheme_id'))
    )
    op.create_table('memory_facts',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.String(length=15), nullable=False),
    sa.Column('fact_text', sa.String(length=300), nullable=False),
    sa.Column('embedding', Vector(1024), nullable=False),
    sa.Column('importance', sa.SmallInteger(), server_default=sa.text('3'), nullable=False),
    sa.Column('source_message_id', sa.Uuid(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("category IN ('preference', 'fact', 'goal_context', 'concern', 'behavior')", name=op.f('ck_memory_facts_category_valid')),
    sa.CheckConstraint('importance >= 1 AND importance <= 5', name=op.f('ck_memory_facts_importance_range')),
    sa.ForeignKeyConstraint(['source_message_id'], ['messages.id'], name=op.f('fk_memory_facts_source_message_id_messages'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_memory_facts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_memory_facts'))
    )
    op.create_index('ix_memory_facts_embedding_hnsw', 'memory_facts', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_index('ix_memory_facts_user_active', 'memory_facts', ['user_id', 'is_active'], unique=False)


def downgrade() -> None:
    # Extensions are left installed; other database objects may depend on them.
    op.drop_index('ix_memory_facts_user_active', table_name='memory_facts')
    op.drop_index('ix_memory_facts_embedding_hnsw', table_name='memory_facts', postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.drop_table('memory_facts')
    op.drop_table('user_scheme_tracking')
    op.drop_index('ix_user_scheme_matches_user_status', table_name='user_scheme_matches')
    op.drop_table('user_scheme_matches')
    op.drop_table('term_feedback')
    op.drop_table('scheme_translations')
    op.drop_table('scheme_steps')
    op.drop_table('scheme_eligibility_rules')
    op.drop_index(op.f('ix_scheme_documents_scheme_id'), table_name='scheme_documents')
    op.drop_table('scheme_documents')
    op.drop_index('ix_messages_conversation_created', table_name='messages')
    op.drop_table('messages')
    op.drop_table('lesson_translations')
    op.drop_table('lesson_progress')
    op.drop_index('ix_goal_contributions_goal_date', table_name='goal_contributions')
    op.drop_table('goal_contributions')
    op.drop_table('glossary_translations')
    op.drop_index(op.f('ix_fraud_reports_text_hash'), table_name='fraud_reports')
    op.drop_table('fraud_reports')
    op.drop_table('emergency_fund_plans')
    op.drop_table('user_profiles')
    op.drop_table('user_learning_stats')
    op.drop_index('ix_transactions_user_type_occurred', table_name='transactions')
    op.drop_index('ix_transactions_user_occurred', table_name='transactions')
    op.drop_table('transactions')
    op.drop_index('ix_schemes_level_state', table_name='schemes')
    op.drop_index(op.f('ix_schemes_category_slug'), table_name='schemes')
    op.drop_table('schemes')
    op.drop_table('risk_snapshots')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_notifications_status_scheduled', table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('notification_settings')
    op.drop_table('lessons')
    op.drop_index('ix_insights_user_read_created', table_name='insights')
    op.drop_table('insights')
    op.drop_index('uq_goals_one_emergency_fund', table_name='goals', postgresql_where=sa.text("category = 'emergency_fund' AND status IN ('active', 'paused')"))
    op.drop_index('ix_goals_user_status', table_name='goals')
    op.drop_table('goals')
    op.drop_table('glossary_terms')
    op.drop_index('ix_fraud_checks_user_created', table_name='fraud_checks')
    op.drop_index(op.f('ix_fraud_checks_text_hash'), table_name='fraud_checks')
    op.drop_table('fraud_checks')
    op.drop_index(op.f('ix_device_tokens_user_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
    op.drop_index('ix_debts_user_status', table_name='debts')
    op.drop_table('debts')
    op.drop_index('ix_conversations_user_last_message', table_name='conversations')
    op.drop_table('conversations')
    op.drop_index('ix_consents_user_type_created', table_name='consents')
    op.drop_table('consents')
    op.drop_table('cashflow_forecasts')
    op.drop_table('budgets')
    op.drop_table('videos')
    op.drop_table('users')
    op.drop_table('scheme_categories')
    op.drop_index('ix_otp_requests_phone_created', table_name='otp_requests')
    op.drop_table('otp_requests')
    op.drop_table('goal_templates')
    op.drop_table('fraud_patterns')

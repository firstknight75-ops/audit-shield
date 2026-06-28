from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'AuditCore'
    environment: str = 'development'
    api_v1_prefix: str = '/api'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 1440
    deployment_mode: Literal['onpremise', 'cloud'] = Field(default='onpremise', alias='DEPLOYMENT_MODE')
    database_url: str = Field(default='postgresql+asyncpg://auditcore:auditcore@postgres:5432/auditcore', alias='DATABASE_URL')
    redis_url: str = Field(default='redis://redis:6379/0', alias='REDIS_URL')
    vault_url: str = Field(default='http://vault:8200', alias='VAULT_URL')
    vault_token: str = Field(default='dev-token', alias='VAULT_TOKEN')
    company_master_key: str = Field(default='local-company-master-key', alias='COMPANY_MASTER_KEY')
    tenant_inventory_schema: str = Field(default='inventory', alias='TENANT_INVENTORY_SCHEMA')
    app_owner_database_url: str | None = Field(default=None, alias='APP_OWNER_DATABASE_URL')
    whatsapp_gateway_url: str = Field(default='http://baileys-bridge:3001', alias='WHATSAPP_GATEWAY_URL')
    cloud_whatsapp_gateway_url: str = Field(default='http://whatsapp-cloud-gateway:3002', alias='CLOUD_WHATSAPP_GATEWAY_URL')
    backup_bucket: str = Field(default='auditcore-backups', alias='BACKUP_BUCKET')


@lru_cache
def get_settings() -> Settings:
    return Settings()

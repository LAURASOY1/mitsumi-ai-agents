from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import json
import boto3
from botocore.exceptions import ClientError
import logging


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Mitsumi AI Agent Platform"
    API_PREFIX: str = "/api"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # AWS Bedrock
    AWS_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    ENVIRONMENT: str = "development"
    USE_AWS_SECRETS: bool = True
    
    SECRET_DATABASE: str = "prod/database"
    SECRET_REDIS: str = "prod/redis"
    SECRET_MONGODB: str = "prod/mongodb"
    SECRET_LLM_KEYS: str = "prod/llm-keys"
    SECRET_JWT: str = "prod/jwt"

    # Google OAuth (Calendar + Gmail)
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""

    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    TAVILY_API_KEY: str = ""

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    AUTH_ALLOWED_DOMAIN: str = "mitsumidistribution.com"
    OTP_EXPIRE_MINUTES: int = 10
    RESET_TOKEN_EXPIRE_MINUTES: int = 15
    OTP_MAX_ATTEMPTS: int = 5

    POSTGRES_URL: str = "postgresql+asyncpg://user:pass@postgres:5432/mitsumi"
    REDIS_URL: str = "redis://redis:6379/0"
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB: str = "mitsumi"

    REDIS_TTL_SECONDS: int = 7200
    REDIS_MEMORY_MAX_MESSAGES: int = 20
    
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 150
    RATE_LIMIT_STORE: str = "redis"
    
    
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_SCRIPT_SRC: str = "'self' 'unsafe-inline'"
    CSP_STYLE_SRC: str = "'self' 'unsafe-inline'"
    
    REQUEST_TIMEOUT: int = 120
    KEEPALIVE_TIMEOUT: int = 5
    CACHE_TTL_SECONDS: int = 300
    CACHE_KEY_PREFIX: str = "mitsumi"
    
    
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False
    SAMPLE_RATE: float = 0.1

    DEV_AUTH_BYPASS_OTP: bool = True
    SUPERADMIN_EMAIL: str = "francis@mitsumidistribution.com"
    SUPERADMIN_NAME: str = "Francis Mitsumi"
    SUPERADMIN_PASSWORD: str = ""

    RESEND_API_KEY: str = ""
    EMAIL_FROM_NAME: str = "Mitsumi AI Platform"
    EMAIL_FROM_ADDRESS: str = "no-reply@mitsumitestlabs.com"
    EMAIL_REPLY_TO: str = "support@mitsumitestlabs.com"
    APP_BASE_URL: str = "http://localhost:3000"

    # Google Calendar (OAuth-less service account). When GOOGLE_CALENDAR_JSON
    # (inline JSON) and GOOGLE_CALENDAR_ID are set, calendar_event tool writes
    # real events; otherwise it falls back to the local JSON log.
    GOOGLE_CALENDAR_JSON: str = ""
    GOOGLE_CALENDAR_ID: str = ""
    GOOGLE_CALENDAR_TIMEZONE: str = "Africa/Nairobi"

    @property
    def is_bedrock(self) -> bool:
        return (self.LLM_PROVIDER or "").strip().lower() in ("bedrock", "aws", "aws_bedrock")

    @property
    def bedrock_ready(self) -> bool:
        return self.is_bedrock and bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY and self.AWS_REGION)

    @property
    def llm_ready(self) -> bool:
        """True when the LLM provider is fully configured."""
        if self.is_bedrock:
            return self.bedrock_ready
        return bool(self.LLM_API_KEY or self.GOOGLE_API_KEY)
    def _get_secret(self, secret_name: str) -> dict:
        """Fetch secret from AWS Secrets Manager"""
        if not self.USE_AWS_SECRETS or self.ENVIRONMENT == "development":
            return {}
        
        try:
            client = boto3.client('secretsmanager', region_name=self.AWS_REGION)
            response = client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Secret {secret_name} not found, using environment")
                return {}
            logger.error(f"Failed to fetch secret {secret_name}: {e}")
            raise
    
    def _get_env_or_secret(self, env_var: str, secret_name: str = None, secret_key: str = None) -> str:
        """Get value from environment or AWS Secret"""
        value = os.getenv(env_var)
        if value:
            return value
        if secret_name and secret_key:
            secret = self._get_secret(secret_name)
            return secret.get(secret_key, "")
        return ""
    # Auto-fetch from AWS
    @property
    def resolved_llm_api_key(self) -> str:
        """Get LLM API key from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_LLM_KEYS)
            return secret.get("openai", self.LLM_API_KEY)
        return self.LLM_API_KEY
    
    @property
    def resolved_google_api_key(self) -> str:
        """Get Google API key from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_LLM_KEYS)
            return secret.get("google", self.GOOGLE_API_KEY)
        return self.GOOGLE_API_KEY
    
    @property
    def resolved_jwt_secret(self) -> str:
        """Get JWT secret from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_JWT)
            return secret.get("secret", self.JWT_SECRET)
        return self.JWT_SECRET
    
    @property
    def resolved_postgres_url(self) -> str:
        """Get PostgreSQL URL from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_DATABASE)
            return f"postgresql+asyncpg://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['database']}"
        return self.POSTGRES_URL
    
    @property
    def resolved_redis_url(self) -> str:
        """Get Redis URL from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_REDIS)
            if secret.get("password"):
                return f"redis://:{secret['password']}@{secret['host']}:{secret['port']}/0"
            return f"redis://{secret['host']}:{secret['port']}/0"
        return self.REDIS_URL
    
    @property
    def resolved_mongodb_url(self) -> str:
        """Get MongoDB URL from secrets in production"""
        if self.ENVIRONMENT == "production":
            secret = self._get_secret(self.SECRET_MONGODB)
            return f"mongodb://{secret['username']}:{secret['password']}@{secret['host']}:{secret['port']}"
        return self.MONGODB_URL

    # LLM HELPER PROPERTIES

    @property
    def is_bedrock(self) -> bool:
        return (self.LLM_PROVIDER or "").strip().lower() in ("bedrock", "aws", "aws_bedrock")
    
    @property
    def bedrock_ready(self) -> bool:
        return self.is_bedrock and bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY and self.AWS_REGION)
    
    @property
    def llm_ready(self) -> bool:
        """True when the LLM provider is fully configured."""
        if self.is_bedrock:
            return self.bedrock_ready
        return bool(self.resolved_llm_api_key or self.resolved_google_api_key)

    # ENVIRONMENT

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_debug(self) -> bool:
        return self.ENVIRONMENT != "production"
    
    # DATABASE READY CHECKS
    
    @property
    def database_ready(self) -> bool:
        return bool(self.resolved_postgres_url)
    
    @property
    def redis_ready(self) -> bool:
        return bool(self.resolved_redis_url)
    
    @property
    def mongodb_ready(self) -> bool:
        return bool(self.resolved_mongodb_url)


    # CORS ORIGINS
    @property
    def cors_origins(self) -> list:
        """Get allowed CORS origins based on environment"""
        if self.is_production:
            return [
                "https://app.mitsumi.ai",
                "https://*.mitsumi.ai",
            ]
        return self.ALLOWED_ORIGINS
    
    
        """Get database connection pool configuration"""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis connection configuration"""
        return {
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "socket_timeout": self.REDIS_SOCKET_TIMEOUT,
            "retry_on_timeout": self.REDIS_RETRY_ON_TIMEOUT,
        }
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
            "allow_methods": self.CORS_ALLOW_METHODS,
            "allow_headers": self.CORS_ALLOW_HEADERS,
        }
    
    def get_security_headers(self) -> dict:
        """Get security headers configuration"""
        return {
            "enabled": self.SECURITY_HEADERS_ENABLED,
            "hsts_max_age": self.HSTS_MAX_AGE,
            "csp_default_src": self.CSP_DEFAULT_SRC,
            "csp_script_src": self.CSP_SCRIPT_SRC,
            "csp_style_src": self.CSP_STYLE_SRC,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
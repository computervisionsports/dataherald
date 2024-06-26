import os
import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, BaseSettings, Extra, Field, validator

from dataherald.utils.encrypt import FernetEncrypt


class LLMCredentials(BaseSettings):
    organization_id: str | None
    api_key: str | None

    @validator("api_key", "organization_id", pre=True, always=True)
    def encrypt(cls, value: str):
        fernet_encrypt = FernetEncrypt()
        try:
            fernet_encrypt.decrypt(value)
            return value
        except Exception:
            return fernet_encrypt.encrypt(value)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class FileStorage(BaseModel):
    name: str
    access_key_id: str
    secret_access_key: str
    region: str | None
    bucket: str

    class Config:
        extra = Extra.ignore

    @validator("access_key_id", "secret_access_key", pre=True, always=True)
    def encrypt(cls, value: str):
        fernet_encrypt = FernetEncrypt()
        try:
            fernet_encrypt.decrypt(value)
            return value
        except Exception:
            return fernet_encrypt.encrypt(value)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class SSHSettings(BaseSettings):
    host: str | None
    username: str | None
    password: str | None
    port: str | None = "22"
    private_key_password: str | None

    class Config:
        extra = Extra.ignore

    @validator("password", "private_key_password", pre=True, always=True)
    def encrypt(cls, value: str):
        fernet_encrypt = FernetEncrypt()
        try:
            fernet_encrypt.decrypt(value)
            return value
        except Exception:
            return fernet_encrypt.encrypt(value)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class InvalidURIFormatError(Exception):
    pass


class SupportedDialects(Enum):
    POSTGRES = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"
    DATABRICKS = "databricks"
    SNOWFLAKE = "snowflake"
    CLICKHOUSE = "clickhouse"
    AWSATHENA = "awsathena"
    DUCKDB = "duckdb"
    BIGQUERY = "bigquery"
    SQLITE = "sqlite"
    REDSHIFT = "redshift"


class DatabaseConnection(BaseModel):
    id: str | None
    alias: str
    dialect: SupportedDialects | None
    use_ssh: bool = False
    connection_uri: str | None
    path_to_credentials_file: str | None
    llm_api_key: str | None = None
    ssh_settings: SSHSettings | None = None
    file_storage: FileStorage | None = None
    metadata: dict | None
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def get_dialect(cls, input_string):
        pattern = r"([^:/]+):/+([^/]+)/?([^/]+)"
        match = re.match(pattern, input_string)
        if not match:
            raise InvalidURIFormatError(f"Invalid URI format: {input_string}")
        return match.group(1)

    @classmethod
    def set_dialect(cls, input_string):
        for dialect in SupportedDialects:
            if dialect.value in input_string:
                return dialect.value
        return None

    @validator("connection_uri", pre=True, always=True)
    def connection_uri_format(cls, value: str, values):
        fernet_encrypt = FernetEncrypt()
        try:
            fernet_encrypt.decrypt(value)
        except Exception:
            dialect_prefix = cls.get_dialect(value)
            values["dialect"] = cls.set_dialect(dialect_prefix)
            value = fernet_encrypt.encrypt(value)
        return value

    @validator("llm_api_key", pre=True, always=True)
    def llm_api_key_encrypt(cls, value: str):
        fernet_encrypt = FernetEncrypt()
        try:
            fernet_encrypt.decrypt(value)
            return value
        except Exception:
            return fernet_encrypt.encrypt(value)

    def decrypt_api_key(self):
        if self.llm_api_key is not None and self.llm_api_key != "":
            fernet_encrypt = FernetEncrypt()
            return fernet_encrypt.decrypt(self.llm_api_key)
        return os.environ.get("OPENAI_API_KEY")

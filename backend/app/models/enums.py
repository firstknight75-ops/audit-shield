import enum


class CompanyTier(str, enum.Enum):
    essential = 'essential'
    advanced = 'advanced'
    elite = 'elite'


class DeploymentMode(str, enum.Enum):
    onpremise = 'onpremise'
    cloud = 'cloud'


class UserRole(str, enum.Enum):
    owner = 'owner'
    gm = 'gm'
    manager = 'manager'
    auditor = 'auditor'
    admin = 'admin'
    appowner = 'appowner'


class OverrideAction(str, enum.Enum):
    grant = 'grant'
    revoke = 'revoke'

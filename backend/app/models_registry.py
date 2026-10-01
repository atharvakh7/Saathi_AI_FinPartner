"""Imports every ORM model so Base.metadata is complete (Alembic autogenerate, create_all)."""

from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.chat import models as chat_models  # noqa: F401
from app.modules.finance import models as finance_models  # noqa: F401
from app.modules.fraud import models as fraud_models  # noqa: F401
from app.modules.goals import models as goals_models  # noqa: F401
from app.modules.insights import models as insights_models  # noqa: F401
from app.modules.learn import models as learn_models  # noqa: F401
from app.modules.memory import models as memory_models  # noqa: F401
from app.modules.notifications import models as notifications_models  # noqa: F401
from app.modules.planner import models as planner_models  # noqa: F401
from app.modules.schemes import models as schemes_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401

from app.repository.csv_repository import CSVRepository
from app.services.finance_service import FinanceService
from app.services.history_service import ConversationHistoryService
from app.services.report_service import ReportService


class ServiceContainer:
    def __init__(self) -> None:
        self.repository = CSVRepository()
        self.finance_service = FinanceService(self.repository)
        self.history_service = ConversationHistoryService()
        self.report_service = ReportService()


container = ServiceContainer()

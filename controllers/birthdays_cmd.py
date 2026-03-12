from ..services.birthday_service import BirthdayService
from src.config.constants import BIRTHDAYS_MAX_DAYS


class BirthdaysCommand:
    def __init__(self):
        self.service = BirthdayService()

    def upcoming(self, days):

        try:
            days_int = int(days)
            if days_int < 0:
                return "Error: Number of days must be positive"

            if days_int > self.MAX_DAYS:
                return f"Error: Number of days cannot exceed {BIRTHDAYS_MAX_DAYS}"

            upcoming_birthdays = self.service.get_upcoming_birthdays(days_int)

            if not upcoming_birthdays:
                return f"No contacts found with birthdays within next {days_int} days"

            result = [f"Contacts with birthdays within next {days_int} days:"]
            for contact in upcoming_birthdays:
                result.append(f"- {contact.name}: {contact.birthday}")

            return "\n".join(result)

        except ValueError:
            return "Error: Number of days must be a number"
        except Exception as e:
            return f"Error searching birthdays: {str(e)}"

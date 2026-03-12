from uuid import UUID

from ..services.contacts_service import ContactsService


class ContactsCommand:
    def __init__(self):
        self.service = ContactsService()

    def add_contact(self, name, phone=None, email=None, address=None, birthday=None):
        try:
            contact_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "birthday": birthday,
            }
            result = self.service.add(contact_data)
            return f"Contact '{name}' successfully added! (ID: {result.id})"
        except Exception as e:
            return f"Error adding contact: {str(e)}"

    def edit_contact(self, contact_id, **kwargs):
        try:
            cid = UUID(contact_id)
            result = self.service.patch(cid, kwargs)
            return f"Contact '{result.name}' successfully updated!"
        except Exception as e:
            return f"Error editing contact: {str(e)}"

    def delete_contact(self, contact_id):
        try:
            cid = UUID(contact_id)
            contact = self.service.get_by_id(cid)
            if not contact:
                return f"Error deleting contact: contact with id {contact_id} not found"
            contact_name = contact.name
            self.service.delete(cid)
            return f"Contact '{contact_name}' successfully deleted!"
        except Exception as e:
            return f"Error deleting contact: {str(e)}"

    def search_contacts(self, query):
        try:
            results = self.service.search(query=query)
            if not results:
                return f"No contacts found for query '{query}'"

            output = ["Contact search results:"]
            for contact in results:
                contact_info = f"{contact.name}"
                if contact.phone:
                    contact_info += f" | Phone: {contact.phone}"
                if contact.email:
                    contact_info += f" | Email: {contact.email}"
                if contact.birthday:
                    contact_info += f" | Birthday: {contact.birthday}"
                output.append(contact_info)

            return "\n".join(output)
        except Exception as e:
            return f"Error during search: {str(e)}"

    def list_contacts(self):
        try:
            contacts = self.service.get_all()
            if not contacts:
                return "Contact list is empty"

            output = ["All contacts:"]
            for i, contact in enumerate(contacts, 1):
                contact_info = f"{i}. {contact.name}"
                if contact.phone:
                    contact_info += f" | Phone: {contact.phone}"
                if contact.email:
                    contact_info += f" | Email: {contact.email}"
                if contact.birthday:
                    contact_info += f" | Birthday: {contact.birthday}"
                output.append(contact_info)

            return "\n".join(output)
        except Exception as e:
            return f"Error getting contact list: {str(e)}"

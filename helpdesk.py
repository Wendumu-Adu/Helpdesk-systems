import abc
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Union

# =====================================================================
# 2.3 Enums für Status und Priorität
# =====================================================================

class TicketStatus(Enum):
    OPEN = auto()
    IN_PROGRESS = auto()
    WAITING = auto()
    RESOLVED = auto()
    CLOSED = auto()


class Priority(Enum):
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


# =====================================================================
# 4. Exception Handling – Fehlerhierarchie
# =====================================================================

class HelpdeskError(Exception):
    """Basisklasse für fachliche Helpdesk-Fehler."""
    pass


class TicketNotFoundError(HelpdeskError):
    """Wird ausgelöst, wenn eine Ticket-ID im System nicht existiert."""
    pass


class InvalidStatusTransitionError(HelpdeskError):
    """Wird ausgelöst, wenn ein unzulässiger Statuswechsel versucht wird."""
    pass


class AssignmentError(HelpdeskError):
    """Basisklasse für Zuweisungsfehler."""
    pass


class CapacityExceededError(AssignmentError):
    """Wird ausgelöst, wenn ein Agent seine maximale Ticketkapazität erreicht hat."""
    pass


class ValidationError(HelpdeskError):
    """Wird ausgelöst, wenn Pflichtfelder ungültig oder Enums falsch sind."""
    pass


# =====================================================================
# 3. Support-Mitarbeiter und Polymorphie
# =====================================================================

class SupportAgent(ABC):
    """Abstrakte Basisklasse für alle Support-Mitarbeiter."""
    
    def __init__(self, agent_id: str, name: str, max_tickets: int):
        if not agent_id or not agent_id.strip():
            raise ValidationError("Agent-ID darf nicht leer sein.")
        if not name or not name.strip():
            raise ValidationError("Name darf nicht leer sein.")
        if max_tickets <= 0:
            raise ValidationError("Die maximale Ticketkapazität muss größer als 0 sein.")
            
        self._agent_id = agent_id
        self._name = name
        self._max_tickets = max_tickets
        self._current_tickets: List[str] = []  # Speichert Ticket-IDs im Arbeitsspeicher

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def max_tickets(self) -> int:
        return self._max_tickets

    @property
    def current_ticket_count(self) -> int:
        return len(self._current_tickets)

    def has_capacity(self) -> bool:
        return len(self._current_tickets) < self._max_tickets

    def add_ticket(self, ticket_id: str) -> None:
        if not self.has_capacity():
            raise CapacityExceededError(f"Agent {self._name} hat maximale Kapazität von {self._max_tickets} erreicht.")
        if ticket_id in self._current_tickets:
            raise AssignmentError(f"Ticket {ticket_id} ist diesem Agent bereits zugewiesen.")
        self._current_tickets.append(ticket_id)

    def remove_ticket(self, ticket_id: str) -> None:
        if ticket_id not in self._current_tickets:
            raise AssignmentError(f"Ticket {ticket_id} ist diesem Agent nicht zugewiesen.")
        self._current_tickets.remove(ticket_id)

    @abstractmethod
    def can_handle(self, ticket: "Ticket") -> bool:
        """Polymorphe Methode zur Überprüfung der Bearbeitungsberechtigung."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._agent_id!r}, name={self._name!r})"


class JuniorAgent(SupportAgent):
    """Darf Tickets mit Priorität LOW und NORMAL bearbeiten."""
    
    def can_handle(self, ticket: "Ticket") -> bool:
        return ticket.priority in (Priority.LOW, Priority.NORMAL)


class SeniorAgent(SupportAgent):
    """Darf alle Prioritäten bearbeiten und kritische Tickets übernehmen."""
    
    def can_handle(self, ticket: "Ticket") -> bool:
        return True


# =====================================================================
# 6.1 Ticket-Historie im Arbeitsspeicher
# =====================================================================

class HistoryEntry:
    """Repräsentiert einen unveränderlichen Eintrag in der Ticket-Historie."""
    
    def __init__(self, action: str, agent_name: str, description: str):
        self._timestamp = datetime.now()
        self._action = action
        self._agent_name = agent_name
        self._description = description

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def action(self) -> str:
        return self._action

    @property
    def agent_name(self) -> str:
        return self._agent_name

    @property
    def description(self) -> str:
        return self._description

    def __str__(self) -> str:
        return f"[{self._timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self._action} von {self._agent_name}: {self._description}"

    def __repr__(self) -> str:
        return f"HistoryEntry({self._action!r}, {self._agent_name!r}, {self._description!r})"


# =====================================================================
# 2.1 & 2.2 Abstrakte Basisklasse Ticket & Subklassen
# =====================================================================

class Ticket(ABC):
    """Abstrakte Basisklasse für Tickets im Helpdesk-System."""
    
    def __init__(self, ticket_id: str, title: str, description: str, priority: Priority, created_by: str):
        if not ticket_id or not ticket_id.strip():
            raise ValidationError("Ticket-ID darf nicht leer sein.")
        if not title or not title.strip():
            raise ValidationError("Titel darf nicht leer sein.")
        if not description or not description.strip():
            raise ValidationError("Beschreibung darf nicht leer sein.")
        if not created_by or not created_by.strip():
            raise ValidationError("Ersteller (created_by) darf nicht leer sein.")
        if not isinstance(priority, Priority):
            raise ValidationError("Ungültiger Prioritätswert.")

        self._ticket_id = ticket_id
        self._title = title
        self._description = description
        self._priority = priority
        self._created_by = created_by
        
        self._status = TicketStatus.OPEN
        self._assigned_to: Optional[SupportAgent] = None
        self._history: List[HistoryEntry] = []
        
        self.add_history_entry("Erstellung", created_by, f"Ticket '{title}' wurde registriert.")

    @property
    def ticket_id(self) -> str:
        return self._ticket_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def priority(self) -> Priority:
        return self._priority

    @property
    def status(self) -> TicketStatus:
        return self._status

    @property
    def created_by(self) -> str:
        return self._created_by

    @property
    def assigned_to(self) -> Optional[SupportAgent]:
        return self._assigned_to

    @property
    def history(self) -> List[HistoryEntry]:
        return list(self._history)

    @abstractmethod
    def get_category(self) -> str:
        """Erzwingt Implementierung einer Kategorisierung in den Subklassen."""
        pass

    def add_history_entry(self, action: str, operator_name: str, desc: str) -> None:
        self._history.append(HistoryEntry(action, operator_name, desc))

    def set_assigned_agent(self, agent: Optional[SupportAgent], operator_name: str) -> None:
        if agent is None:
            old_agent_name = self._assigned_to.name if self._assigned_to else "Niemand"
            self._assigned_to = None
            self.add_history_entry("Zuweisung entfernt", operator_name, f"Zuweisung von {old_agent_name} wurde aufgehoben.")
            return

        if self._assigned_to == agent:
            raise AssignmentError(f"Ticket {self._ticket_id} ist bereits an {agent.name} zugewiesen.")
            
        if not agent.can_handle(self):
            raise AssignmentError(f"{agent.__class__.__name__} {agent.name} darf keine {self._priority.name}-Tickets bearbeiten.")

        self._assigned_to = agent
        self.add_history_entry("Zuweisung", operator_name, f"Zugewiesen an {agent.name}.")

    def update_status(self, new_status: TicketStatus, operator_name: str) -> None:
        if not isinstance(new_status, TicketStatus):
            raise ValidationError("Ungültiger Statuswert.")
            
        if self._status == new_status:
            return

        if self._status == TicketStatus.CLOSED:
            raise InvalidStatusTransitionError("Ein geschlossenes Ticket (CLOSED) darf nicht wieder geöffnet werden.")
        if self._status == TicketStatus.OPEN and new_status == TicketStatus.CLOSED:
            raise InvalidStatusTransitionError("Ein Ticket im Status OPEN darf nicht direkt geschlossen (CLOSED) werden.")

        old_status = self._status
        self._status = new_status
        self.add_history_entry("Statusänderung", operator_name, f"Status geändert: {old_status.name} -> {new_status.name}")

    # =====================================================================
    # 6.2 Dunder-Methoden für strukturierten Systemvergleich
    # =====================================================================
    def __str__(self) -> str:
        agent_name = self._assigned_to.name if self._assigned_to else "Nicht zugewiesen"
        return f"[{self._ticket_id}] {self._title} ({self._status.name}) - Prio: {self._priority.name} - Bearbeiter: {agent_name}"

    def __repr__(self) -> str:
        return f"Ticket(id={self._ticket_id!r}, title={self._title!r}, status={self._status!r})"


# Konkrete Ticket-Subklassen
class HardwareTicket(Ticket):
    def get_category(self) -> str:
        return "Hardware"


class SoftwareTicket(Ticket):
    def get_category(self) -> str:
        return "Software"


# =====================================================================
# Interaktive Test-/Demo-Funktion
# =====================================================================
def interactive_menu():
    print("=" * 80)
    print("                          Helpdisk System")
    print("=" * 80)
    # 1. Mitarbeiter erstellen
    junior = JuniorAgent("A001", "Adeday B.", 2)
    senior = SeniorAgent("A002", "Mearey K.", 3)
    
    # 2. Tickets erstellen
    t1 = HardwareTicket("T-101", "Drucker defekt", "Der Drucker im 2. Stock druckt nur noch Streifen.", Priority.NORMAL, "Kahsay")
    t2 = SoftwareTicket("T-102", "Datenbank-Fehler", "Produktionsserver meldet Deadlocks!", Priority.CRITICAL, "Berhane")
    
    print("Erstellte Tickets: ")
    print("=" * 18 )
    
    
    print(t1 )
    print(t2 )
    print("=" * 80)
    
    # 3. Zuweisung testen
    try:
        t1.set_assigned_agent(junior, "System")
        t1.update_status(TicketStatus.IN_PROGRESS, "Adeday B")
        print("\nErfolgreiche Zuweisung von T-101 an Junior-Agent:")
        print(t1)
    except HelpdeskError as e:
        print(f"Fehler: {e}")
        
    # 4. Einschränkung testen (Junior darf kein Critical-Ticket annehmen)
    try:
        print("\nVersuch, kritisches Ticket an Junior-Agenten zu übergeben...")
        t2.set_assigned_agent(junior, "System")
    except HelpdeskError as e:
        print(f"Erwarteter Fehler abgefangen: {e}")
        
    # 5. Zuweisung an Senior-Agenten
    try:
        t2.set_assigned_agent(senior, "System")
        t2.update_status(TicketStatus.IN_PROGRESS, "Mearey K")
        print("\nErfolgreiche Zuweisung von T-102 an Senior-Agent:")
        print(t2)
    except HelpdeskError as e:
        print(f"Fehler: {e}")

    # 6. Historie ausgeben
    print("\n" + "=" * 80)
    print(f"Vollständige Historie für Ticket {t1.ticket_id}:")
    for entry in t1.history:
        print(entry)


if __name__ == "__main__":
    interactive_menu()
# panel_registry.py

class PanelRegistry:
    def __init__(self):
        self._registry = {}

    def register_panel(self, panel_id, panel_instance):
        """
        Register a new panel instance.
        :param panel_id: Unique identifier for the panel.
        :param panel_instance: Instance of the panel to register.
        """
        if panel_id in self._registry:
            raise ValueError(f"Panel ID {panel_id} is already registered.")
        self._registry[panel_id] = panel_instance

    def deregister_panel(self, panel_id):
        """
        Deregister a panel instance.
        :param panel_id: Unique identifier for the panel to deregister.
        """
        if panel_id in self._registry:
            del self._registry[panel_id]
        else:
            raise ValueError(f"Panel ID {panel_id} not found in registry.")

    def get_panel_instance(self, panel_id):
        """
        Retrieve a panel instance by its ID.
        :param panel_id: Unique identifier for the panel.
        :return: Panel instance associated with the given ID, or None if not found.
        """
        return self._registry.get(panel_id, None)

    def list_panels(self):
        """
        List all registered panel IDs.
        :return: List of registered panel IDs.
        """
        return list(self._registry.keys())

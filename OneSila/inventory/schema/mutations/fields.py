from .mutation_classes import CreateInventoryMovementMutation, UpdateWithPublicIdMutation
from ..types.input import InventoryMovementInput, InventoryMovementPartialInput


def create_inventory_movement():
    extensions = []
    return CreateInventoryMovementMutation(InventoryMovementInput, extensions=extensions)


def update_inventory_movement():
    extensions = []
    return UpdateWithPublicIdMutation(InventoryMovementPartialInput, extensions=extensions)

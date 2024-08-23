# Adding a New Inspector Block Checker

This guide outlines the steps to add a new inspector block checker for product validation.

## Step 1: Define a New Error Code

1. Open the `constants.py` file.
2. Define a new error code:

    ```python
    NEW_ERROR_CODE = 103  # Example
    ```

3. Add the error code to the `ERROR_TYPES` tuple with a description.

    ```python
    ERROR_TYPES = (
        (NEW_ERROR_CODE, _('Description of the new error')),
        # Other error codes...
    )
    ```

## Step 2: Create the Block Configuration

1. In `constants.py`, define the block configuration:

    ```python
    new_block_config = {
        'error_code': NEW_ERROR_CODE,
        'simple_product_applicability': REQUIRED,
        'configurable_product_applicability': NONE,
        'manufacturable_product_applicability': REQUIRED,
        'bundle_product_applicability': REQUIRED,
        'dropship_product_applicability': REQUIRED,
        'supplier_product_applicability': NONE,
    }
    ```

2. Add the new block configuration to the `blocks` list:

    ```python
    blocks = [existing_block, new_block_config]
    ```

## Step 3: Create the QuerySet and Manager

1. Define a custom QuerySet:

    ```python
    class NewInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
        pass
    ```

2. Define a custom Manager:

    ```python
    class NewInspectorBlockManager(InspectorBlockManager):
        def get_queryset(self):
            return NewInspectorBlockQuerySet(self.model, using=self._db)
    ```

## Step 4: Create the Proxy Model

1. Implement the proxy model for the new checker:

    ```python
    class NewInspectorBlock(InspectorBlock):
        from .constants import new_block_config

        objects = NewInspectorBlockManager()
        proxy_filter_fields = new_block_config

        class Meta:
            proxy = True
            verbose_name = _("Inspector Block New Check")
    ```

## Step 5: Create Signals

1. Define success and failure signals:

    ```python
    inspector_new_block_failed = ModelSignal(use_caching=True)
    inspector_new_block_success = ModelSignal(use_caching=True)
    ```

## Step 6: Create a Factory Override

1. Create a factory class for the new checker:

    ```python
    @InspectorBlockFactoryRegistry.register(NEW_ERROR_CODE)
    class NewInspectorBlockFactory(InspectorBlockFactory):
        def __init__(self, block, save_inspector=True):
            super().__init__(block, success_signal=inspector_new_block_success, failure_signal=inspector_new_block_failed, save_inspector=save_inspector)

        def _check(self):
            if some_condition_is_not_met:
                raise InspectorBlockFailed("Description of why the block failed.")
    ```

## Step 7: Connect the Receivers

1. Connect signals to trigger the checker when relevant model changes occur. Use the following pattern:

    ```python
    @receiver(post_save, sender=RelevantModel)
    @receiver(post_delete, sender=RelevantModel)
    def relevant_model_change_handler(sender, instance, **kwargs):
        inspector_block_refresh.send(
            sender=instance.product.inspector.__class__,
            instance=instance.product.inspector,
            error_code=NEW_ERROR_CODE,
            run_async=False
        )
    ```

## Step 8: Write Tests for the New Inspector Block

1. Write a test case to validate the functionality:

    ```python
    from core.tests import TestCase

    class NewInspectorBlockTest(TestCase):
        def setUp(self):
            # Set up product and inspector
            pass

        def test_new_block_functionality(self):
            # Test the new block's behavior
            pass
    ```

2. Run the tests:

    ```bash
    python manage.py test products_inspector
    ```

## Step 9: Update the Frontend

1. **Translations**: Add translations for the new error code.
2. **Fix Button Logic**: Update the `errorMap` in the frontend to include the new error code and appropriate navigation path.

---

This README provides the steps necessary to create and integrate a new inspector block checker, ensuring a consistent approach across the codebase.

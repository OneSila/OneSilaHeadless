from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator

registry = DemoDataLibrary()

# # Demo-data generators can be used as method, like the public and private examples below.
# @registry.register_private_app
# def populate_private_some_data(multi_tenant_company):
#     demo_data = {
#         'first_name': faker.first_name()
#         'field_other': (function, {"kwarg": 393}),
#         'field_value': 12121,
#     }
#     baker.make("MyModel", **demo_data)
#
# # A demo-data generator for a public app could look like:
# @registry.register_public_app
# def populate_some_public_data():
#     demo_data = {
#         'first_name': faker.first_name()
#     }
#     baker.make("MyModel", **demo_data)

# # They can also be classes, subclassed from PrivateDataGenerator or PublicDataGenerator
# @registry.register_private_app
# class AppModelPrivateGenerator(PrivateDataGenerator):
#     model = PrivateModel
#     count = 10
#     field_mapper = {
#         'first_name': fake.fist_name,
#         'last_name': fake.last_name,
#    }
#
# @registry.register_public_app
# class AppModelPublicGenerator(PublicDataGenerator):
#     model = PublicModel
#     count = 10
#     field_mapper = {
#         'unit': some_data_generating_method,
#    }

import json
import logging
import tablib
from io import BytesIO

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.test import Client as DjangoClient
from rest_framework.parsers import JSONParser

from ambulance.models import Ambulance
from emstrack.tests.util import date2iso
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from login.resources import UserResource
from login.serializers import ClientSerializer
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestUserResource(TestSetup):

    def setUp(self):

        # call super
        super().setUp()

        self.resource = UserResource()

        self.dataset = tablib.Dataset(headers=['id', 'username', 'first_name', 'last_name', 'email',
                                               'is_staff', 'is_dispatcher', 'is_active'])
        row = [self.u5.id, 'change', 'first', 'last', 'email@email.com', False, True, True]
        self.dataset.append(row)

    def test_get_instance(self):
        instance_loader = self.resource._meta.instance_loader_class(self.resource)
        self.resource._meta.import_id_fields = ['id']

        instance = self.resource.get_instance(instance_loader,
                                              self.dataset.dict[0])
        self.assertEqual(instance, self.u5.id)

    def test_get_instance_when_id_fields_not_in_dataset(self):
        self.resource._meta.import_id_fields = ['id']

        # construct a dataset with a missing "id" column
        dataset = tablib.Dataset(headers=['name', 'author_email', 'price'])
        dataset.append(['Some book', 'test@example.com', "10.25"])

        instance_loader = self.resource._meta.instance_loader_class(self.resource)

        with mock.patch.object(instance_loader, 'get_instance') as mocked_method:
            result = self.resource.get_instance(instance_loader, dataset.dict[0])
            # Resource.get_instance() should return None
            self.assertIs(result, None)
            # instance_loader.get_instance() should NOT have been called
            mocked_method.assert_not_called()

    def test_get_export_headers(self):
        headers = self.resource.get_export_headers()
        self.assertEqual(headers, ['published_date', 'id', 'name', 'author',
                                   'author_email', 'published_time', 'price',
                                   'added',
                                   'categories', ])

    def test_export(self):
        dataset = self.resource.export(Book.objects.all())
        self.assertEqual(len(dataset), 1)

    def test_export_iterable(self):
        dataset = self.resource.export(list(Book.objects.all()))
        self.assertEqual(len(dataset), 1)

    def test_get_diff(self):
        diff = Diff(self.resource, self.book, False)
        book2 = Book(name="Some other book")
        diff.compare_with(self.resource, book2)
        html = diff.as_html()
        headers = self.resource.get_export_headers()
        self.assertEqual(html[headers.index('name')],
                         '<span>Some </span><ins style="background:#e6ffe6;">'
                         'other </ins><span>book</span>')
        self.assertFalse(html[headers.index('author_email')])

    @skip("See: https://github.com/django-import-export/django-import-export/issues/311")
    def test_get_diff_with_callable_related_manager(self):
        resource = AuthorResource()
        author = Author(name="Some author")
        author.save()
        author2 = Author(name="Some author")
        self.book.author = author
        self.book.save()
        diff = Diff(self.resource, author, False)
        diff.compare_with(self.resource, author2)
        html = diff.as_html()
        headers = resource.get_export_headers()
        self.assertEqual(html[headers.index('books')],
                         '<span>core.Book.None</span>')

    def test_import_data(self):
        result = self.resource.import_data(self.dataset, raise_errors=True)

        self.assertFalse(result.has_errors())
        self.assertEqual(len(result.rows), 1)
        self.assertTrue(result.rows[0].diff)
        self.assertEqual(result.rows[0].import_type,
                         results.RowResult.IMPORT_TYPE_UPDATE)

        instance = Book.objects.get(pk=self.book.pk)
        self.assertEqual(instance.author_email, 'test@example.com')
        self.assertEqual(instance.price, Decimal("10.25"))

    def test_import_data_raises_field_specific_validation_errors(self):
        resource = AuthorResource()
        dataset = tablib.Dataset(headers=['id', 'name', 'birthday'])
        dataset.append(['', 'A.A.Milne', '1882test-01-18'])

        result = resource.import_data(dataset, raise_errors=False)

        self.assertTrue(result.has_validation_errors())
        self.assertIs(result.rows[0].import_type, results.RowResult.IMPORT_TYPE_INVALID)
        self.assertIn('birthday', result.invalid_rows[0].field_specific_errors)

    def test_import_data_handles_widget_valueerrors_with_unicode_messages(self):
        resource = AuthorResourceWithCustomWidget()
        dataset = tablib.Dataset(headers=['id', 'name', 'birthday'])
        dataset.append(['', 'A.A.Milne', '1882-01-18'])

        result = resource.import_data(dataset, raise_errors=False)

        self.assertTrue(result.has_validation_errors())
        self.assertIs(result.rows[0].import_type, results.RowResult.IMPORT_TYPE_INVALID)
        self.assertEqual(
            result.invalid_rows[0].field_specific_errors['name'],
            ["Ова вриједност је страшна!"]
        )

    def test_model_validation_errors_not_raised_when_clean_model_instances_is_false(self):

        class TestResource(resources.ModelResource):
            class Meta:
                model = Author
                clean_model_instances = False

        resource = TestResource()
        dataset = tablib.Dataset(headers=['id', 'name'])
        dataset.append(['', '123'])

        result = resource.import_data(dataset, raise_errors=False)
        self.assertFalse(result.has_validation_errors())
        self.assertEqual(len(result.invalid_rows), 0)

    def test_model_validation_errors_raised_when_clean_model_instances_is_true(self):

        class TestResource(resources.ModelResource):
            class Meta:
                model = Author
                clean_model_instances = True
                export_order = ['id', 'name', 'birthday']

        # create test dataset
        # NOTE: column order is deliberately strange
        dataset = tablib.Dataset(headers=['name', 'id'])
        dataset.append(['123', '1'])

        # run import_data()
        resource = TestResource()
        result = resource.import_data(dataset, raise_errors=False)

        # check has_validation_errors()
        self.assertTrue(result.has_validation_errors())

        # check the invalid row itself
        invalid_row = result.invalid_rows[0]
        self.assertEqual(invalid_row.error_count, 1)
        self.assertEqual(
            invalid_row.field_specific_errors,
            {'name': ["'123' is not a valid value"]}
        )
        # diff_header and invalid_row.values should match too
        self.assertEqual(
            result.diff_headers,
            ['id', 'name', 'birthday']
        )
        self.assertEqual(
            invalid_row.values,
            ('1', '123', '---')
        )

    def test_known_invalid_fields_are_excluded_from_model_instance_cleaning(self):

        # The custom widget on the parent class should complain about
        # 'name' first, preventing Author.full_clean() from raising the
        # error as it does in the previous test

        class TestResource(AuthorResourceWithCustomWidget):
            class Meta:
                model = Author
                clean_model_instances = True

        resource = TestResource()
        dataset = tablib.Dataset(headers=['id', 'name'])
        dataset.append(['', '123'])

        result = resource.import_data(dataset, raise_errors=False)
        self.assertTrue(result.has_validation_errors())
        self.assertEqual(result.invalid_rows[0].error_count, 1)
        self.assertEqual(
            result.invalid_rows[0].field_specific_errors,
            {'name': ["Ова вриједност је страшна!"]}
        )

    def test_import_data_error_saving_model(self):
        row = list(self.dataset.pop())
        # set pk to something that would yield error
        row[0] = 'foo'
        self.dataset.append(row)
        result = self.resource.import_data(self.dataset, raise_errors=False)

        self.assertTrue(result.has_errors())
        self.assertTrue(result.rows[0].errors)
        actual = result.rows[0].errors[0].error
        self.assertIsInstance(actual, ValueError)
        self.assertIn("could not convert string to float", str(actual))

    def test_import_data_delete(self):

        class B(BookResource):
            delete = fields.Field(widget=widgets.BooleanWidget())

            def for_delete(self, row, instance):
                return self.fields['delete'].clean(row)

        row = [self.book.pk, self.book.name, '1']
        dataset = tablib.Dataset(*[row], headers=['id', 'name', 'delete'])
        result = B().import_data(dataset, raise_errors=True)
        self.assertFalse(result.has_errors())
        self.assertEqual(result.rows[0].import_type,
                         results.RowResult.IMPORT_TYPE_DELETE)
        self.assertFalse(Book.objects.filter(pk=self.book.pk))

    def test_save_instance_with_dry_run_flag(self):
        class B(BookResource):
            def before_save_instance(self, instance, using_transactions, dry_run):
                super().before_save_instance(instance, using_transactions, dry_run)
                if dry_run:
                    self.before_save_instance_dry_run = True
                else:
                    self.before_save_instance_dry_run = False
            def save_instance(self, instance, using_transactions=True, dry_run=False):
                super().save_instance(instance, using_transactions, dry_run)
                if dry_run:
                    self.save_instance_dry_run = True
                else:
                    self.save_instance_dry_run = False
            def after_save_instance(self, instance, using_transactions, dry_run):
                super().after_save_instance(instance, using_transactions, dry_run)
                if dry_run:
                    self.after_save_instance_dry_run = True
                else:
                    self.after_save_instance_dry_run = False

        resource = B()
        resource.import_data(self.dataset, dry_run=True, raise_errors=True)
        self.assertTrue(resource.before_save_instance_dry_run)
        self.assertTrue(resource.save_instance_dry_run)
        self.assertTrue(resource.after_save_instance_dry_run)

        resource.import_data(self.dataset, dry_run=False, raise_errors=True)
        self.assertFalse(resource.before_save_instance_dry_run)
        self.assertFalse(resource.save_instance_dry_run)
        self.assertFalse(resource.after_save_instance_dry_run)

    def test_delete_instance_with_dry_run_flag(self):
        class B(BookResource):
            delete = fields.Field(widget=widgets.BooleanWidget())

            def for_delete(self, row, instance):
                return self.fields['delete'].clean(row)

            def before_delete_instance(self, instance, dry_run):
                super().before_delete_instance(instance, dry_run)
                if dry_run:
                    self.before_delete_instance_dry_run = True
                else:
                    self.before_delete_instance_dry_run = False

            def delete_instance(self, instance, using_transactions=True, dry_run=False):
                super().delete_instance(instance, using_transactions, dry_run)
                if dry_run:
                    self.delete_instance_dry_run = True
                else:
                    self.delete_instance_dry_run = False

            def after_delete_instance(self, instance, dry_run):
                super().after_delete_instance(instance, dry_run)
                if dry_run:
                    self.after_delete_instance_dry_run = True
                else:
                    self.after_delete_instance_dry_run = False

        resource = B()
        row = [self.book.pk, self.book.name, '1']
        dataset = tablib.Dataset(*[row], headers=['id', 'name', 'delete'])
        resource.import_data(dataset, dry_run=True, raise_errors=True)
        self.assertTrue(resource.before_delete_instance_dry_run)
        self.assertTrue(resource.delete_instance_dry_run)
        self.assertTrue(resource.after_delete_instance_dry_run)

        resource.import_data(dataset, dry_run=False, raise_errors=True)
        self.assertFalse(resource.before_delete_instance_dry_run)
        self.assertFalse(resource.delete_instance_dry_run)
        self.assertFalse(resource.after_delete_instance_dry_run)

    def test_relationships_fields(self):

        class B(resources.ModelResource):
            class Meta:
                model = Book
                fields = ('author__name',)

        author = Author.objects.create(name="Author")
        self.book.author = author
        resource = B()
        result = resource.fields['author__name'].export(self.book)
        self.assertEqual(result, author.name)

    def test_dehydrating_fields(self):

        class B(resources.ModelResource):
            full_title = fields.Field(column_name="Full title")

            class Meta:
                model = Book
                fields = ('author__name', 'full_title')

            def dehydrate_full_title(self, obj):
                return '%s by %s' % (obj.name, obj.author.name)

        author = Author.objects.create(name="Author")
        self.book.author = author
        resource = B()
        full_title = resource.export_field(resource.get_fields()[0], self.book)
        self.assertEqual(full_title, '%s by %s' % (self.book.name,
                                                   self.book.author.name))

    def test_widget_fomat_in_fk_field(self):
        class B(resources.ModelResource):

            class Meta:
                model = Book
                fields = ('author__birthday',)
                widgets = {
                    'author__birthday': {'format': '%Y-%m-%d'},
                }

        author = Author.objects.create(name="Author")
        self.book.author = author
        resource = B()
        result = resource.fields['author__birthday'].export(self.book)
        self.assertEqual(result, str(date.today()))

    def test_widget_kwargs_for_field(self):

        class B(resources.ModelResource):

            class Meta:
                model = Book
                fields = ('published',)
                widgets = {
                    'published': {'format': '%d.%m.%Y'},
                }

        resource = B()
        self.book.published = date(2012, 8, 13)
        result = resource.fields['published'].export(self.book)
        self.assertEqual(result, "13.08.2012")

    def test_foreign_keys_export(self):
        author1 = Author.objects.create(name='Foo')
        self.book.author = author1
        self.book.save()

        dataset = self.resource.export(Book.objects.all())
        self.assertEqual(dataset.dict[0]['author'], author1.pk)

    def test_foreign_keys_import(self):
        author2 = Author.objects.create(name='Bar')
        headers = ['id', 'name', 'author']
        row = [None, 'FooBook', author2.pk]
        dataset = tablib.Dataset(row, headers=headers)
        self.resource.import_data(dataset, raise_errors=True)

        book = Book.objects.get(name='FooBook')
        self.assertEqual(book.author, author2)

    def test_m2m_export(self):
        cat1 = Category.objects.create(name='Cat 1')
        cat2 = Category.objects.create(name='Cat 2')
        self.book.categories.add(cat1)
        self.book.categories.add(cat2)

        dataset = self.resource.export(Book.objects.all())
        self.assertEqual(dataset.dict[0]['categories'],
                         '%d,%d' % (cat1.pk, cat2.pk))

    def test_m2m_import(self):
        cat1 = Category.objects.create(name='Cat 1')
        headers = ['id', 'name', 'categories']
        row = [None, 'FooBook', str(cat1.pk)]
        dataset = tablib.Dataset(row, headers=headers)
        self.resource.import_data(dataset, raise_errors=True)

        book = Book.objects.get(name='FooBook')
        self.assertIn(cat1, book.categories.all())

    def test_m2m_options_import(self):
        cat1 = Category.objects.create(name='Cat 1')
        cat2 = Category.objects.create(name='Cat 2')
        headers = ['id', 'name', 'categories']
        row = [None, 'FooBook', "Cat 1|Cat 2"]
        dataset = tablib.Dataset(row, headers=headers)

        class BookM2MResource(resources.ModelResource):
            categories = fields.Field(
                attribute='categories',
                widget=widgets.ManyToManyWidget(Category, field='name',
                                                separator='|')
            )

            class Meta:
                model = Book

        resource = BookM2MResource()
        resource.import_data(dataset, raise_errors=True)
        book = Book.objects.get(name='FooBook')
        self.assertIn(cat1, book.categories.all())
        self.assertIn(cat2, book.categories.all())

    def test_related_one_to_one(self):
        # issue #17 - Exception when attempting access something on the
        # related_name

        user = User.objects.create(username='foo')
        profile = Profile.objects.create(user=user)
        Entry.objects.create(user=user)
        Entry.objects.create(user=User.objects.create(username='bar'))

        class EntryResource(resources.ModelResource):
            class Meta:
                model = Entry
                fields = ('user__profile', 'user__profile__is_private')

        resource = EntryResource()
        dataset = resource.export(Entry.objects.all())
        self.assertEqual(dataset.dict[0]['user__profile'], profile.pk)
        self.assertEqual(dataset.dict[0]['user__profile__is_private'], '1')
        self.assertEqual(dataset.dict[1]['user__profile'], '')
        self.assertEqual(dataset.dict[1]['user__profile__is_private'], '')

    def test_empty_get_queryset(self):
        # issue #25 - Overriding queryset on export() fails when passed
        # queryset has zero elements
        dataset = self.resource.export(Book.objects.none())
        self.assertEqual(len(dataset), 0)

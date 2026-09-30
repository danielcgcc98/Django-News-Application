from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

from .models import Article, Publisher, Newsletter


User = get_user_model()


class NewsApplicationTests(TestCase):

    def setUp(self):
        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        self.reader = User.objects.create_user(
            username="reader1",
            password="password123",
            role="Reader",
            email="reader@example.com"
        )

        self.journalist = User.objects.create_user(
            username="journalist1",
            password="password123",
            role="Journalist",
            email="journalist@example.com"
        )

        self.editor = User.objects.create_user(
            username="editor1",
            password="password123",
            role="Editor",
            email="editor@example.com"
        )

        # -------------------------------------------------
        # PUBLISHER
        # -------------------------------------------------

        self.publisher = Publisher.objects.create(
            name="Test Publisher"
        )

        # -------------------------------------------------
        # ARTICLE
        # -------------------------------------------------

        self.article = Article.objects.create(
            title="Test Article",
            content="This is test article content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False
        )

        self.approved_article = Article.objects.create(
            title="Approved Article",
            content="This article has been approved.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True
        )

    # =====================================================
    # ARTICLE LIST TESTS
    # =====================================================

    def test_article_list_requires_login(self):
        response = self.client.get(
            reverse("article_list")
        )

        self.assertNotEqual(response.status_code, 200)

    def test_reader_can_view_article_list(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.get(
            reverse("article_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Approved Article"
        )

    def test_unapproved_article_not_shown_to_reader(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.get(
            reverse("article_list")
        )

        self.assertNotContains(
            response,
            "Test Article"
        )

    # =====================================================
    # ARTICLE DETAIL TESTS
    # =====================================================

    def test_reader_can_view_approved_article(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "article_detail",
                args=[self.approved_article.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Approved Article"
        )

    def test_reader_cannot_view_unapproved_article(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "article_detail",
                args=[self.article.id]
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_view_own_unapproved_article(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "article_detail",
                args=[self.article.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Test Article"
        )

    # =====================================================
    # JOURNALIST CREATE TESTS
    # =====================================================

    def test_journalist_can_create_article(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.post(
            reverse("article_create"),
            {
                "title": "New Test Article",
                "content": "New article content.",
                "publisher": self.publisher.id,
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Article.objects.filter(
                title="New Test Article"
            ).exists()
        )

        new_article = Article.objects.get(
            title="New Test Article"
        )

        self.assertEqual(
            new_article.author,
            self.journalist
        )

        self.assertFalse(
            new_article.approved
        )

    def test_reader_cannot_create_article(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.post(
            reverse("article_create"),
            {
                "title": "Unauthorized Article",
                "content": "This should not be created.",
                "publisher": self.publisher.id,
            }
        )

        self.assertEqual(
            response.status_code,
            403
        )

        self.assertFalse(
            Article.objects.filter(
                title="Unauthorized Article"
            ).exists()
        )

    def test_journalist_cannot_create_article_without_required_fields(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.post(
            reverse("article_create"),
            {
                "title": "",
                "content": "",
                "publisher": self.publisher.id,
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            Article.objects.filter(
                title=""
            ).exists()
        )

    # =====================================================
    # JOURNALIST EDIT TESTS
    # =====================================================

    def test_journalist_can_edit_own_article(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.post(
            reverse(
                "article_edit",
                args=[self.article.id]
            ),
            {
                "title": "Updated Article",
                "content": "Updated content.",
                "publisher": self.publisher.id,
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.title,
            "Updated Article"
        )

        self.assertEqual(
            self.article.content,
            "Updated content."
        )

        # Editing sends the article back for approval.
        self.assertFalse(
            self.article.approved
        )

    def test_journalist_cannot_edit_another_users_article(self):
        another_journalist = User.objects.create_user(
            username="journalist2",
            password="password123",
            role="Journalist",
            email="journalist2@example.com"
        )

        other_article = Article.objects.create(
            title="Other Article",
            content="Other content.",
            author=another_journalist,
            publisher=self.publisher,
            approved=False
        )

        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.post(
            reverse(
                "article_edit",
                args=[other_article.id]
            ),
            {
                "title": "Unauthorized Update",
                "content": "Unauthorized content.",
                "publisher": self.publisher.id,
            }
        )

        self.assertEqual(
            response.status_code,
            404
        )

    # =====================================================
    # ARTICLE DELETE TESTS
    # =====================================================

    def test_journalist_can_delete_own_article(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        article_id = self.article.id

        response = self.client.post(
            reverse(
                "article_delete",
                args=[article_id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            Article.objects.filter(
                id=article_id
            ).exists()
        )

    def test_reader_cannot_delete_article(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.post(
            reverse(
                "article_delete",
                args=[self.article.id]
            )
        )

        self.assertEqual(
            response.status_code,
            403
        )

        self.assertTrue(
            Article.objects.filter(
                id=self.article.id
            ).exists()
        )

    # =====================================================
    # EDITOR APPROVAL TESTS
    # =====================================================

    @patch("news.views.send_mail")
    def test_editor_can_approve_article(self, mock_send_mail):
        self.client.login(
            username="editor1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "approve_article",
                args=[self.article.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.article.refresh_from_db()

        self.assertTrue(
            self.article.approved
        )

    def test_reader_cannot_approve_article(self):
        self.client.login(
            username="reader1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "approve_article",
                args=[self.article.id]
            )
        )

        self.assertEqual(
            response.status_code,
            403
        )

        self.article.refresh_from_db()

        self.assertFalse(
            self.article.approved
        )

    def test_journalist_cannot_approve_article(self):
        self.client.login(
            username="journalist1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "approve_article",
                args=[self.article.id]
            )
        )

        self.assertEqual(
            response.status_code,
            403
        )

        self.article.refresh_from_db()

        self.assertFalse(
            self.article.approved
        )

    # =====================================================
    # SUBSCRIPTION TESTS
    # =====================================================

    def test_reader_can_subscribe_to_journalist(self):
        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.assertTrue(
            self.reader.subscribed_journalists.filter(
                id=self.journalist.id
            ).exists()
        )

    def test_reader_can_subscribe_to_publisher(self):
        self.reader.subscribed_publishers.add(
            self.publisher
        )

        self.assertTrue(
            self.reader.subscribed_publishers.filter(
                id=self.publisher.id
            ).exists()
        )

    # =====================================================
    # NEWSLETTER TESTS
    # =====================================================

    def test_journalist_can_create_newsletter_model(self):
        newsletter = Newsletter.objects.create(
            title="Weekly News",
            content="This is the weekly newsletter.",
            author=self.journalist
        )

        newsletter.articles.add(
            self.approved_article
        )

        self.assertEqual(
            newsletter.title,
            "Weekly News"
        )

        self.assertEqual(
            newsletter.author,
            self.journalist
        )

        self.assertTrue(
            newsletter.articles.filter(
                id=self.approved_article.id
            ).exists()
        )

    # =====================================================
    # PUBLISHER / ARTICLE RELATIONSHIP
    # =====================================================

    def test_article_can_belong_to_publisher(self):
        self.assertEqual(
            self.article.publisher,
            self.publisher
        )

        self.assertTrue(
            self.publisher.articles.filter(
                id=self.article.id
            ).exists()
        )

    # =====================================================
    # EMAIL NOTIFICATION TEST
    # =====================================================

    @patch("news.views.send_mail")
    def test_approval_sends_email_to_subscriber(
        self,
        mock_send_mail
    ):
        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.client.login(
            username="editor1",
            password="password123"
        )

        response = self.client.get(
            reverse(
                "approve_article",
                args=[self.article.id]
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            mock_send_mail.called
        )

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertIn(
            "reader@example.com",
            call_kwargs["recipient_list"]
        )
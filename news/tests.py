"""Automated tests for the news website views and REST API permissions."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Article, Newsletter, Publisher


User = get_user_model()


class NewsApplicationTests(APITestCase):
    """Test website workflows and REST API permissions."""
    def setUp(self):
        """Create representative users, publishers, and articles."""
        self.reader = User.objects.create_user(
            username="reader1",
            password="password123",
            role="Reader",
            email="reader@example.com",
        )
        self.journalist = User.objects.create_user(
            username="journalist1",
            password="password123",
            role="Journalist",
            email="journalist@example.com",
        )
        self.other_journalist = User.objects.create_user(
            username="journalist2",
            password="password123",
            role="Journalist",
            email="other@example.com",
        )
        self.editor = User.objects.create_user(
            username="editor1",
            password="password123",
            role="Editor",
            email="editor@example.com",
        )
        self.publisher = Publisher.objects.create(name="Test Publisher")
        self.other_publisher = Publisher.objects.create(name="Other Publisher")

        self.article = Article.objects.create(
            title="Test Article",
            content="Test article content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )
        self.approved_article = Article.objects.create(
            title="Approved Article",
            content="Approved article content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.other_article = Article.objects.create(
            title="Other Approved Article",
            content="Other content.",
            author=self.other_journalist,
            publisher=self.other_publisher,
            approved=True,
        )

    def login(self, user):
        """Log a test user into the website."""
        self.client.login(username=user.username, password="password123")

    def api_login(self, user):
        """Authenticate the API client as the supplied user."""
        self.client.force_authenticate(user=user)

    # Website authentication/access
    def test_article_list_requires_login(self):
        """Test the article list requires login workflow."""
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("article_list"))
        self.assertEqual(response.status_code, 302)

    def test_reader_can_view_approved_articles(self):
        """Test the reader can view approved articles workflow."""
        self.login(self.reader)
        response = self.client.get(reverse("article_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved Article")
        self.assertNotContains(response, "Test Article")

    def test_reader_cannot_view_pending_article(self):
        """Test the reader cannot view pending article workflow."""
        self.login(self.reader)
        response = self.client.get(
            reverse("article_detail", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_view_pending_article(self):
        """Test the editor can view pending article workflow."""
        self.login(self.editor)
        response = self.client.get(
            reverse("article_detail", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 200)

    # Article website CRUD
    def test_journalist_can_create_article(self):
        """Test the journalist can create article workflow."""
        self.login(self.journalist)
        response = self.client.post(
            reverse("article_create"),
            {
                "title": "New Article",
                "content": "New content.",
                "publisher": self.publisher.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        new_article = Article.objects.get(title="New Article")
        self.assertEqual(new_article.author, self.journalist)
        self.assertFalse(new_article.approved)

    def test_reader_cannot_create_article(self):
        """Test the reader cannot create article workflow."""
        self.login(self.reader)
        response = self.client.post(
            reverse("article_create"),
            {"title": "No", "content": "No"},
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_edit_own_article(self):
        """Test the journalist can edit own article workflow."""
        self.login(self.journalist)
        response = self.client.post(
            reverse("article_edit", args=[self.article.id]),
            {
                "title": "Updated Article",
                "content": "Updated content.",
                "publisher": self.publisher.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Article")
        self.assertFalse(self.article.approved)

    def test_journalist_cannot_edit_another_article(self):
        """Test the journalist cannot edit another article workflow."""
        self.login(self.journalist)
        response = self.client.post(
            reverse("article_edit", args=[self.other_article.id]),
            {"title": "Unauthorized", "content": "No"},
        )
        self.assertEqual(response.status_code, 404)

    def test_editor_can_edit_any_article(self):
        """Test the editor can edit any article workflow."""
        self.login(self.editor)
        response = self.client.post(
            reverse("article_edit", args=[self.article.id]),
            {
                "title": "Editor Updated",
                "content": "Editor content.",
                "publisher": self.publisher.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Editor Updated")

    def test_editor_can_delete_any_article(self):
        """Test the editor can delete any article workflow."""
        self.login(self.editor)
        response = self.client.post(
            reverse("article_delete", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_reader_cannot_delete_article(self):
        """Test the reader cannot delete article workflow."""
        self.login(self.reader)
        response = self.client.post(
            reverse("article_delete", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 403)

    # Approval workflow
    @patch("news.views.requests.post")
    @patch("news.views.send_mail")
    def test_editor_can_approve_and_notify(
        self,
        mock_send_mail,
        mock_post,
    ):
        """Test the editor approval and subscriber notification workflow."""
        mock_post.return_value.raise_for_status.return_value = None
        self.reader.subscribed_journalists.add(self.journalist)
        self.login(self.editor)

        response = self.client.post(
            reverse("approve_article", args=[self.article.id])
        )

        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)
        self.assertTrue(mock_send_mail.called)
        self.assertIn(
            "reader@example.com",
            mock_send_mail.call_args.kwargs["recipient_list"],
        )
        self.assertTrue(mock_post.called)

    def test_reader_cannot_approve(self):
        """Test the reader cannot approve workflow."""
        self.login(self.reader)
        response = self.client.post(
            reverse("approve_article", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 403)
        self.article.refresh_from_db()
        self.assertFalse(self.article.approved)

    def test_approve_requires_post(self):
        """Test the approve requires post workflow."""
        self.login(self.editor)
        response = self.client.get(
            reverse("approve_article", args=[self.article.id])
        )
        self.assertEqual(response.status_code, 405)

    # Subscriptions
    def test_reader_can_subscribe_to_journalist(self):
        """Test the reader can subscribe to journalist workflow."""
        self.reader.subscribed_journalists.add(self.journalist)
        self.assertIn(
            self.journalist,
            self.reader.subscribed_journalists.all(),
        )

    def test_reader_can_subscribe_to_publisher(self):
        """Test the reader can subscribe to publisher workflow."""
        self.reader.subscribed_publishers.add(self.publisher)
        self.assertIn(
            self.publisher,
            self.reader.subscribed_publishers.all(),
        )

    # Newsletters
    def test_reader_can_view_newsletters(self):
        """Test the reader can view newsletters workflow."""
        newsletter = Newsletter.objects.create(
            title="Weekly News",
            description="A weekly collection of news.",
            author=self.journalist,
        )
        newsletter.articles.add(self.approved_article)
        self.login(self.reader)
        response = self.client.get(reverse("newsletter_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly News")

    def test_journalist_can_create_newsletter(self):
        """Test the journalist can create newsletter workflow."""
        self.login(self.journalist)
        response = self.client.post(
            reverse("newsletter_create"),
            {
                "title": "Journalist Newsletter",
                "description": "Journalist description.",
                "articles": [self.approved_article.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        newsletter = Newsletter.objects.get(title="Journalist Newsletter")
        self.assertEqual(newsletter.author, self.journalist)

    def test_editor_can_create_newsletter(self):
        """Test the editor can create newsletter workflow."""
        self.login(self.editor)
        response = self.client.post(
            reverse("newsletter_create"),
            {
                "title": "Editor Newsletter",
                "description": "Editor description.",
                "articles": [self.approved_article.id],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Newsletter.objects.filter(title="Editor Newsletter").exists()
        )

    def test_reader_cannot_create_newsletter(self):
        """Test the reader cannot create newsletter workflow."""
        self.login(self.reader)
        response = self.client.post(
            reverse("newsletter_create"),
            {"title": "No", "description": "No"},
        )
        self.assertEqual(response.status_code, 403)

    # REST API authentication/authorization
    def test_api_requires_authentication(self):
        """Test the api requires authentication workflow."""
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 401)

    def test_reader_can_get_approved_articles(self):
        """Test the reader can get approved articles workflow."""
        self.api_login(self.reader)
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data]
        self.assertIn("Approved Article", titles)
        self.assertNotIn("Test Article", titles)

    def test_reader_gets_only_subscribed_content(self):
        """Test the reader gets only subscribed content workflow."""
        self.reader.subscribed_journalists.add(self.journalist)
        self.api_login(self.reader)
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data]
        self.assertIn("Approved Article", titles)
        self.assertNotIn("Other Approved Article", titles)

    def test_non_reader_cannot_get_subscribed_content(self):
        """Test the non reader cannot get subscribed content workflow."""
        self.api_login(self.journalist)
        response = self.client.get("/api/articles/subscribed/")
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_article_api(self):
        """Test the journalist can create article api workflow."""
        self.api_login(self.journalist)
        response = self.client.post(
            "/api/articles/",
            {
                "title": "API Article",
                "content": "Created through API.",
                "publisher": self.publisher.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(title="API Article")
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

    def test_reader_cannot_create_article_api(self):
        """Test the reader cannot create article api workflow."""
        self.api_login(self.reader)
        response = self.client.post(
            "/api/articles/",
            {"title": "Blocked", "content": "Blocked"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_update_own_article_api(self):
        """Test the journalist can update own article api workflow."""
        self.api_login(self.journalist)
        response = self.client.put(
            f"/api/articles/{self.article.id}/",
            {"title": "API Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "API Updated")
        self.assertFalse(self.article.approved)

    def test_editor_can_delete_article_api(self):
        """Test the editor can delete article api workflow."""
        self.api_login(self.editor)
        response = self.client.delete(
            f"/api/articles/{self.article.id}/"
        )
        self.assertEqual(response.status_code, 204)

    def test_reader_cannot_update_article_api(self):
        """Test the reader cannot update article api workflow."""
        self.api_login(self.reader)
        response = self.client.put(
            f"/api/articles/{self.article.id}/",
            {"title": "Blocked"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_newsletter_api_create_and_view(self):
        """Test the newsletter api create and view workflow."""
        self.api_login(self.journalist)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "API Newsletter",
                "description": "API newsletter description.",
                "articles": [self.approved_article.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        self.api_login(self.reader)
        response = self.client.get("/api/newsletters/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["title"], "API Newsletter")

    def test_reader_cannot_manage_newsletters_api(self):
        """Test the reader cannot manage newsletters api workflow."""
        self.api_login(self.reader)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Blocked Newsletter",
                "description": "Blocked",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_approved_log_endpoint_requires_editor(self):
        """Test the approved log endpoint requires editor workflow."""
        self.api_login(self.reader)
        response = self.client.post(
            "/api/approved/",
            {"article_id": self.article.id, "title": self.article.title},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_approved_log_endpoint_accepts_editor(self):
        """Test the approved log endpoint accepts editor workflow."""
        self.api_login(self.editor)
        response = self.client.post(
            "/api/approved/",
            {"article_id": self.article.id, "title": self.article.title},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["approved"])

    def test_article_create_page_shows_input_fields(self):
        """Ensure the article form renders visible labels and inputs."""
        self.login(self.journalist)
        response = self.client.get(reverse("article_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Article title")
        self.assertContains(response, "Article content")
        self.assertContains(response, "Publisher (optional)")
        self.assertContains(response, "Publish immediately as an independent article")

    def test_journalist_can_publish_independent_article(self):
        """Test the journalist can publish independent article workflow."""
        """Ensure an independent journalist article can be approved at creation."""
        self.login(self.journalist)
        response = self.client.post(reverse("article_create"), {"title": "Independent Story", "content": "Independent story content.", "publisher": "", "approve_independent": "on"})
        self.assertEqual(response.status_code, 302)
        article = Article.objects.get(title="Independent Story")
        self.assertIsNone(article.publisher)
        self.assertTrue(article.approved)

    def test_newsletter_form_only_contains_approved_articles(self):
        """Test the newsletter form only contains approved articles workflow."""
        """Ensure the website newsletter form excludes pending articles."""
        from .forms import NewsletterForm
        form = NewsletterForm()
        article_ids = set(form.fields["articles"].queryset.values_list("id", flat=True))
        self.assertIn(self.approved_article.id, article_ids)
        self.assertNotIn(self.article.id, article_ids)

    def test_journalist_can_edit_own_newsletter(self):
        """Test the journalist can edit own newsletter workflow."""
        """Ensure a journalist can edit a newsletter they own."""
        newsletter = Newsletter.objects.create(title="Own Newsletter", description="Own description.", author=self.journalist)
        self.login(self.journalist)
        response = self.client.post(reverse("newsletter_edit", args=[newsletter.id]), {"title": "Updated Newsletter", "description": "Updated.", "articles": [self.approved_article.id]})
        self.assertEqual(response.status_code, 302)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.title, "Updated Newsletter")

    def test_journalist_cannot_edit_other_newsletter(self):
        """Test the journalist cannot edit other newsletter workflow."""
        """Ensure journalists cannot edit another user's newsletter."""
        newsletter = Newsletter.objects.create(title="Other Newsletter", description="Other description.", author=self.other_journalist)
        self.login(self.journalist)
        response = self.client.post(reverse("newsletter_edit", args=[newsletter.id]), {"title": "Unauthorized", "description": "No"})
        self.assertEqual(response.status_code, 403)

    def test_journalist_cannot_delete_other_newsletter(self):
        """Test the journalist cannot delete other newsletter workflow."""
        """Ensure journalists cannot delete another user's newsletter."""
        newsletter = Newsletter.objects.create(title="Other Newsletter", description="Other description.", author=self.other_journalist)
        self.login(self.journalist)
        response = self.client.post(reverse("newsletter_delete", args=[newsletter.id]))
        self.assertEqual(response.status_code, 403)

    def test_editor_can_create_publisher_frontend(self):
        """Test the editor can create publisher frontend workflow."""
        """Ensure an editor can create and staff a publisher from the website."""
        self.login(self.editor)
        response = self.client.post(reverse("publisher_create"), {"name": "Frontend Publisher", "editors": [self.editor.id], "journalists": [self.journalist.id]})
        self.assertEqual(response.status_code, 302)
        publisher = Publisher.objects.get(name="Frontend Publisher")
        self.assertIn(self.editor, publisher.editors.all())
        self.assertIn(self.journalist, publisher.journalists.all())

    def test_reader_can_manage_subscriptions_frontend(self):
        """Test the reader can manage subscriptions frontend workflow."""
        """Ensure readers can subscribe and unsubscribe from the website."""
        self.login(self.reader)
        response = self.client.post(reverse("subscription_manager"), {"subscription_type": "journalist", "object_id": self.journalist.id, "action": "subscribe"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.reader.subscribed_journalists.filter(id=self.journalist.id).exists())
        response = self.client.post(reverse("subscription_manager"), {"subscription_type": "journalist", "object_id": self.journalist.id, "action": "unsubscribe"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.reader.subscribed_journalists.filter(id=self.journalist.id).exists())

    def test_non_reader_cannot_manage_subscriptions_frontend(self):
        """Test the non reader cannot manage subscriptions frontend workflow."""
        """Ensure only readers can use the website subscription manager."""
        self.login(self.journalist)
        response = self.client.get(reverse("subscription_manager"))
        self.assertEqual(response.status_code, 403)

    def test_non_editor_cannot_create_publisher_frontend(self):
        """Test the non editor cannot create publisher frontend workflow."""
        """Ensure publisher creation is restricted to editors."""
        self.login(self.journalist)
        response = self.client.post(reverse("publisher_create"), {"name": "Blocked Publisher"})
        self.assertEqual(response.status_code, 403)

    def test_api_rejects_unapproved_article_in_newsletter(self):
        """Test the api rejects unapproved article in newsletter workflow."""
        """Ensure the REST newsletter endpoint rejects pending articles."""
        self.api_login(self.journalist)
        response = self.client.post("/api/newsletters/", {"title": "Bad Newsletter", "description": "Contains pending content.", "articles": [self.article.id]}, format="json")
        self.assertEqual(response.status_code, 400)

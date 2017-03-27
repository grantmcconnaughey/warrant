import boto3
from django.contrib.auth import get_user_model

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.module_loading import import_string
from django.views.generic import FormView
from django.views.generic.list import MultipleObjectMixin, ListView

from django.conf import settings
from warrant import UserObj


class GetCognitoUserMixin(object):

    def get_user_object(self):
        cog_client = boto3.client('cognito-idp')
        user = cog_client.get_user(AccessToken=self.request.user.access_token)
        u = UserObj(username=user.get('UserAttributes').get('username'),
                    attribute_list=user.get('UserAttributes'))
        return u

    def get_queryset(self):
        u = self.get_user_object()
        my_plans = self.client.get_usage_plans(keyId=u.api_key_id)
        return my_plans.get('items',[])


class MySubsriptions(LoginRequiredMixin,GetCognitoUserMixin,ListView):
    template_name = 'warrant/subscriptions.html'
    client = boto3.client('apigateway')


class AdminSubscriptions(UserPassesTestMixin,GetCognitoUserMixin,
                         MultipleObjectMixin,FormView):
    template_name = 'warrant/admin-subscriptions.html'


    def test_func(self):
        return self.request.user.has_perm('can_edit')

    def get_form_class(self):
        return import_string(settings.WARRANT_SUBSCRIPTION_FORM)

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = self.object_list = self.get_queryset()
        context = super(AdminSubscriptions, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        
        super(AdminSubscriptions, self).form_valid(form)
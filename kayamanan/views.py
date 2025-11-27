from django.shortcuts import render

def dashboard_view(request):
    # Debug: Check which URLs exist
    from django.urls import reverse
    try:
        # Test all the URLs used in base.html
        test_urls = [
            ('account_login', reverse('account_login')),
            ('account_logout', reverse('account_logout')),
            ('account_signup', reverse('account_signup')),
            ('dashboard', reverse('dashboard')),
        ]
        print("URLs that work:", test_urls)
    except Exception as e:
        print("URL that fails:", str(e))
    
    return render(request, 'dashboard.html')
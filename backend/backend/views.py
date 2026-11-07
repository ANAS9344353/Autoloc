from django.http import HttpResponse


def home(request):
    return HttpResponse(
        "<h1>AutoLoc API - Backend Django + MySQL + JWT</h1>"
        "<p>Bienvenue. Voir les endpoints disponibles : "
        "<a href=\"/api/\">/api/</a></p>"
        "<p>Admin Django : <a href=\"/admin/\">/admin/</a></p>",
        content_type="text/html",
    )


def api_index(request):
    return HttpResponse(
        "<h1>Endpoints API</h1>"
        "<h3>Authentification (JWT)</h3>"
        "<ul>"
        "<li>POST <a href=\"/api/signup/\">/api/signup/</a> - inscription</li>"
        "<li>POST <a href=\"/api/login/\">/api/login/</a> - connexion</li>"
        "<li>POST /api/token/refresh/ - rafraichir un access token</li>"
        "<li>POST /api/token/verify/ - verifier un token</li>"
        "</ul>"
        "<h3>Voitures (CRUD)</h3>"
        "<ul>"
        "<li>GET/POST <a href=\"/api/mes-voitures/\">/api/mes-voitures/</a></li>"
        "<li>GET/PUT/PATCH/DELETE /api/mes-voitures/&lt;id&gt;/</li>"
        "<li>GET <a href=\"/api/voitures-proprietaires/\">/api/voitures-proprietaires/</a></li>"
        "<li>GET <a href=\"/api/liste-voitures/\">/api/liste-voitures/</a> (fusionnee)</li>"
        "</ul>"
        "<h3>Reservations</h3>"
        "<ul>"
        "<li>POST /api/reservations/</li>"
        "<li>GET /api/mes-reservations-proprietaire/</li>"
        "<li>GET /api/mes-reservations-client/</li>"
        "<li>PATCH /api/reservations/&lt;id&gt;/accepter/</li>"
        "<li>PATCH /api/reservations/&lt;id&gt;/rejeter/</li>"
        "</ul>",
        content_type="text/html",
    )

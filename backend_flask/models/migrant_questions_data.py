TRAINING_DATA = [
    # Santé
    ("Comment puis-je obtenir une carte de santé ?", {"cats": {"Santé": 1.0}}),
    ("Où puis-je trouver un médecin qui parle ma langue ?", {"cats": {"Santé": 1.0}}),
    ("Comment fonctionne le système de santé ici ?", {"cats": {"Santé": 1.0}}),
    ("Ai-je droit à des soins médicaux gratuits ?", {"cats": {"Santé": 1.0}}),
    ("Comment prendre rendez-vous avec un spécialiste ?", {"cats": {"Santé": 1.0}}),

    # Titre de séjour
    ("Quelles sont les démarches pour renouveler mon titre de séjour ?", {"cats": {"Titre de séjour": 1.0}}),
    ("Quels documents dois-je fournir pour ma demande de titre de séjour ?", {"cats": {"Titre de séjour": 1.0}}),
    ("Combien de temps dure la procédure de demande de titre de séjour ?", {"cats": {"Titre de séjour": 1.0}}),
    ("Puis-je travailler avec un titre de séjour temporaire ?", {"cats": {"Titre de séjour": 1.0}}),
    ("Comment faire une demande de résidence permanente ?", {"cats": {"Titre de séjour": 1.0}}),

    # Cours de français
    ("Où puis-je trouver des cours de français gratuits ?", {"cats": {"Cours de français": 1.0}}),
    ("Y a-t-il des cours du soir pour apprendre le français ?", {"cats": {"Cours de français": 1.0}}),
    ("Existe-t-il des cours de français en ligne ?", {"cats": {"Cours de français": 1.0}}),
    ("Comment puis-je évaluer mon niveau de français ?", {"cats": {"Cours de français": 1.0}}),
    ("Y a-t-il des groupes de conversation en français pour pratiquer ?", {"cats": {"Cours de français": 1.0}}),

    # Travail
    ("Comment chercher un emploi en tant que migrant ?", {"cats": {"Travail": 1.0}}),
    ("Ai-je besoin d'un permis de travail spécial ?", {"cats": {"Travail": 1.0}}),
    ("Comment faire reconnaître mes diplômes pour travailler ici ?", {"cats": {"Travail": 1.0}}),
    ("Quels sont mes droits en tant que travailleur migrant ?", {"cats": {"Travail": 1.0}}),
    ("Où puis-je trouver de l'aide pour rédiger mon CV ?", {"cats": {"Travail": 1.0}}),
    ("Je suis étudiant boursier avec un permis B réfugié. Si je veux travailler, combien d'heures puis-je travailler ?", {"cats": {"Travail": 1.0}}),

    # Logement
    ("Quelles sont les aides au logement pour les nouveaux arrivants ?", {"cats": {"Logement": 1.0}}),
    ("Comment trouver un logement abordable ?", {"cats": {"Logement": 1.0}}),
    ("Quels documents sont nécessaires pour louer un appartement ?", {"cats": {"Logement": 1.0}}),
    ("Existe-t-il des logements sociaux pour les migrants ?", {"cats": {"Logement": 1.0}}),
    ("Comment payer une caution pour un logement ?", {"cats": {"Logement": 1.0}}),

    # Assurances
    ("Comment souscrire à une assurance maladie ?", {"cats": {"Assurances": 1.0}}),
    ("L'assurance habitation est-elle obligatoire ?", {"cats": {"Assurances": 1.0}}),
    ("Quelles assurances sont indispensables en tant que migrant ?", {"cats": {"Assurances": 1.0}}),
    ("Comment choisir la meilleure assurance santé ?", {"cats": {"Assurances": 1.0}}),
    ("Puis-je bénéficier d'une assurance chômage ?", {"cats": {"Assurances": 1.0}}),

    # Aides sociales
    ("Ai-je droit à des aides sociales en tant que migrant ?", {"cats": {"Aides sociales": 1.0}}),
    ("Comment demander des allocations familiales ?", {"cats": {"Aides sociales": 1.0}}),
    ("Existe-t-il des aides financières pour les migrants en difficulté ?", {"cats": {"Aides sociales": 1.0}}),
    ("Quelles sont les conditions pour bénéficier du RSA ?", {"cats": {"Aides sociales": 1.0}}),
    ("Où puis-je trouver des informations sur les aides au logement ?", {"cats": {"Aides sociales": 1.0}}),
    ("J'ai besoin de lunettes, puis-je les obtenir avec l’aide sociale ?", {"cats": {"Aides sociales": 1.0}}),

    # Impôts
    ("Comment déclarer mes impôts dans mon nouveau pays de résidence ?", {"cats": {"Impôts": 1.0}}),
    ("Dois-je payer des impôts sur mes revenus étrangers ?", {"cats": {"Impôts": 1.0}}),
    ("Quelles sont les déductions fiscales auxquelles j'ai droit en tant que migrant ?", {"cats": {"Impôts": 1.0}}),
    ("Comment obtenir un numéro fiscal ?", {"cats": {"Impôts": 1.0}}),
    ("Y a-t-il des impôts locaux à payer ?", {"cats": {"Impôts": 1.0}}),

    # Formation
    ("Quelles formations sont disponibles pour les migrants ?", {"cats": {"Formation": 1.0}}),
    ("Comment s'inscrire à l'université en tant qu'étudiant étranger ?", {"cats": {"Formation": 1.0}}),
    ("Existe-t-il des bourses d'études pour les migrants ?", {"cats": {"Formation": 1.0}}),
    ("Comment faire reconnaître mes qualifications étrangères ?", {"cats": {"Formation": 1.0}}),
    ("Y a-t-il des formations professionnelles gratuites ?", {"cats": {"Formation": 1.0}}),

    # État civil
    ("Comment obtenir un acte de naissance dans mon nouveau canton ?", {"cats": {"État civil": 1.0}}),
    ("Quelles sont les démarches pour se marier ici ?", {"cats": {"État civil": 1.0}}),
    ("Comment changer mon nom de famille officiellement ?", {"cats": {"État civil": 1.0}}),
    ("Où puis-je déclarer la naissance de mon enfant ?", {"cats": {"État civil": 1.0}}),
    ("Comment obtenir un certificat de décès pour un proche ?", {"cats": {"État civil": 1.0}}),

    # Vie pratique
    ("Où puis-je échanger mon permis de conduire ?", {"cats": {"Vie pratique": 1.0}}),
    ("Comment ouvrir un compte bancaire en tant que migrant ?", {"cats": {"Vie pratique": 1.0}}),
    ("Où puis-je recycler mes déchets ?", {"cats": {"Vie pratique": 1.0}}),
    ("Comment fonctionne le système de transport public ?", {"cats": {"Vie pratique": 1.0}}),
    ("Où puis-je trouver des cours de cuisine locale ?", {"cats": {"Vie pratique": 1.0}}),

    # Vie sociale
    ("Comment rencontrer d'autres personnes dans ma nouvelle ville ?", {"cats": {"Vie sociale": 1.0}}),
    ("Existe-t-il des clubs ou associations pour les migrants ?", {"cats": {"Vie sociale": 1.0}}),
    ("Où puis-je pratiquer ma religion ?", {"cats": {"Vie sociale": 1.0}}),
    ("Y a-t-il des événements culturels pour les communautés étrangères ?", {"cats": {"Vie sociale": 1.0}}),
    ("Comment puis-je faire du bénévolat dans ma communauté ?", {"cats": {"Vie sociale": 1.0}}),

    # Droits politiques
    ("Quels sont mes droits politiques en tant que migrant ?", {"cats": {"Droits politiques": 1.0}}),
    ("Puis-je voter aux élections locales ?", {"cats": {"Droits politiques": 1.0}}),
    ("Comment puis-je participer à la vie politique de ma communauté ?", {"cats": {"Droits politiques": 1.0}}),
    ("Quelles sont les conditions pour obtenir la nationalité ?", {"cats": {"Droits politiques": 1.0}}),
    ("Ai-je le droit de manifester pacifiquement ?", {"cats": {"Droits politiques": 1.0}}),

    # Interprétation
    ("Où puis-je trouver un interprète pour m'aider dans mes démarches ?", {"cats": {"Interprétation": 1.0}}),
    ("Y a-t-il des services de traduction gratuits pour les migrants ?", {"cats": {"Interprétation": 1.0}}),
    ("Comment puis-je obtenir une traduction officielle de mes documents ?", {"cats": {"Interprétation": 1.0}}),
    ("Existe-t-il des applications de traduction recommandées ?", {"cats": {"Interprétation": 1.0}}),
    ("Où puis-je trouver un interprète médical ?", {"cats": {"Interprétation": 1.0}}),

    # Arrivée
    ("Quelles sont les premières démarches à faire en arrivant dans le pays ?", {"cats": {"Arrivée": 1.0}}),
    ("Dois-je m'enregistrer auprès des autorités locales à mon arrivée ?", {"cats": {"Arrivée": 1.0}}),
    ("Comment obtenir une carte SIM locale ?", {"cats": {"Arrivée": 1.0}}),
    ("Où puis-je trouver un hébergement temporaire à mon arrivée ?", {"cats": {"Arrivée": 1.0}}),
    ("Quels sont les objets essentiels à apporter lors de mon déménagement ?", {"cats": {"Arrivée": 1.0}}),

    # Contacts utiles
    ("Où puis-je trouver les contacts des associations d'aide aux migrants ?", {"cats": {"Contacts utiles": 1.0}}),
    ("Quel est le numéro d'urgence à appeler en cas de besoin ?", {"cats": {"Contacts utiles": 1.0}}),
    ("Comment contacter l'ambassade de mon pays d'origine ?", {"cats": {"Contacts utiles": 1.0}}),
    ("Où puis-je trouver un avocat spécialisé en droit des étrangers ?", {"cats": {"Contacts utiles": 1.0}}),
    ("Quels sont les services sociaux que je peux contacter pour obtenir de l'aide ?", {"cats": {"Contacts utiles": 1.0}})
]

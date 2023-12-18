1] Configuration de l'environnement de développement

    Prérequis:
        - Anaconda avec python 3.8
        - OTB 7.1.0

    (Compatibilité Linux/Windows)


    1-1] installation de Anaconda (https://docs.anaconda.com/free/anaconda/install/)

        - Linux (https://docs.anaconda.com/free/anaconda/install/linux/):

            # Replace the version number in the installer name, if necessary
            curl -O https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-x86_64.sh

            # Exécution du script precedent
            ./Anaconda3-2020.05-Linux-x86_64.sh

            # initialisation de conda
            conda init

        - Windows
            cf documentation anaconda : https://docs.anaconda.com/free/anaconda/install/windows/


    1-2] création d'un environnement anaconda
        cf documentation anaconda : https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

         conda create --name otb_test_meoss python=3.8
         conda activate otb_test_meoss

    1-3] installation de OTB
        cf documentation otb : https://www.orfeo-toolbox.org/CookBook/Installation.html

        conda install -c orfeotoolbox otb

    1-4] récupération du code source
        git clone https://github.com/Ofni/meoss_ndvi_calculation.git

    1-5] utilisation du script

        # se positionner dans le répertoire du code source
        cd meoss_ndvi_calculation

        python ndvi_calculation.py -h
        python ndvi_calculation.py concat -h
        python ndvi_calculation.py band -h

        python ndvi_calculation.py -i <input_folder> band  -f S2-2A
        python ndvi_calculation.py -i <input_folder> -o <output_folder> concat  *ConcatenateImageBGRPIR

        python ndvi_calculation.py -i /home/guillaume/Recrutement_test_dev/cas1_env-afo/01_data/ concat *BGRPIR
        python ndvi_calculation.py -i /home/guillaume/Recrutement_test_dev/ band -f S2-2A

        nb: le script ndvi_calculation.py fonctionne nativement avec l'environnement env-otb sur le serveur meoss.



2] description du code source et de la démarche de développement

    2-1] process suivi pour le merge des deux scripts

        - J'ai comparé le temps d'exécution du scripts TestRecrutement_ndvi_calculation avec l'option numpy puis OTB.
                sur mon portable personnel l'utilisation d'OTB dure environ 0:40 min contre 1:30s avec numpy.
                sur le serveur de meoss l'utilisation d'OTB ou de numpy semble identique et dure moins de 2s

        A la vue de ces résultats, de la simplicité de la version OTB j'ai décidé de conserver uniquement la version OTB et de supprimer la version numpy.

        Afin de mieux comprendre la différence entre TestRecrutement_ndvi_calculation.py et Bloc1_ndvi.py j'ai entrepris dans un premier temps de simplifier
        et restructurer les  deux scripts afin de les rendre plus lisible et plus facilement  compréhensible et comparable.

        cette étape m'a permis de dégager des fonctions communes et de les factoriser dans un fichier file_management.py notamment pour la recherche des fichiers.
        ces fonctions peuvent être utilisées comme un module python externe et utiliser dans d'autres scripts. la fonction search_B4_B8 peut facilement être enrichie pour de nouveau
		format et/ou band ou bien être utiliser dans un script plus général de recherche de fichiers
        j'ai aussi créé une fonction pour uniformiser le nom de sortie des fichiers.

        n'ayant pas les connaissance suffisante pour déterminer les cas d'utilisation entre Bloc1_ndvi.py et TestRecrutement_ndvi_calculation.py et du fait qu'ils n'utilisent pas exactement les même paramètres d'entré.
		j'ai décidé de conserver les deux approches.

        durant le merge je me suis aussi attaché à mettre de la cohérence dans les noms de variables, de fonctions et de les rendre le plus explicite possible.
        (ajout de commentaires, docstring, etc)

        à la fin de mon processus de merge j'ai aussi créer des fonctions pour gérer les appels à OTB. l'idée étant de simplifier les appels aux modules d'OTB pour éviter l'écriture de nombreuse ligne de code souvent identiques.

        En terme de bonnes pratiques j'ai aussi rajouter un logger (configuré sur la sortie standard mais facilement modifiable pour écrire dans un fichier), quelques tests unitaires, et quelques de gestion d'erreur.

        Concernant git j'ai essayé de créer des commit les plus lisible possible pour suivre simplement le cheminement parcouru.

        Toujours dans un soucis d'homogénéisation et de maintenance/évolution future J'ai remplacé les appels à la CLI d'OTB par l'API python d'OTB.
        Pour par exemple ajouter plus tard des log, gérer les erreurs, du mulit tache, et rester le plus possible dans un environnement "programmable".

        l'ensemble des fonctions additionnelles ont été placé dans un répertoire meoss_lib et "configurer" en tant que package python. l'idée est de pouvoir au choix en faire un module
		à part entière ou plus simplement de mettre ce package dans un dosser git propre et le lié aux autres scripts via des sous module git



    2-2] description des fonctions (cf docstring dans le code source pour plus de détails)

        le fichier  file_managements.py

            il contient l'ensemble des fonctions permettant de gérer les fichiers recherche, renommage, etc. à compléter en fonction des besoins.

            - list_files(pattern=['*'], directory=os.getcwd(), extension='tif', subfolder=False):

                permet de lister les fichiers à partir d'un dossier de départ. la recherche s'effectue en fonction d'un pattern (style unix avec * et ?) et d'un extension de fichier.
                la recherche peut être récursive dans les sous dossiers ou non.

                par default cette fonction recherche tous les fichiers .tif dans le dossier courant.

            - search_B4_B8(input_directory, img_format, subfolder=True)

                permet de rechercher les fichiers B4 et B8 et mask cloud dans un dossier. la recherche se base sur le format des fichiers pour déterminer automatiquement les bon pattern de recherche.
                comme précédemment la recherche peut être récursive dans les sous dossiers ou non. cette fonction utilise la fonction list_files
                la fonction peut facilement être enrichie pour de nouveau format et/ou band ou bien être utiliser dans un script plus général de recherche de fichiers


            - generate_output_file_name(file, format, prefix='', prefix2='', suffix='')

                permet d'obtenir un nom de fichier de sortie en fonction du nom du fichier d'entrée et de paramètres optionnels.
                l'intérêt de cette fonction est d'avoir un nom de sortie constant quelque soit le format d'entrée

                exemple :

                    >>> generate_output_file_name('/var/data/SENTINEL2A_20231012-105856-398_L2A_T31TCJ_D_V3-1.tif', format='S2-A2', prefix='NDVI', prefix2='prefix2', suffix='suffix')
                        retourne : NDVI_prefix2_T31TCJ_20231012T105856_suffix.tif

                fonction à adapter en suivant les besoins et les use cases.
                l'utilisation de cette fonction garantie la cohérence des noms de fichiers de sortie pour tous les scripts l'utilisant.


		le fichier otb.py

			il contient toutes les fonctions pour interragir avec otb de maniere plus simple. Il s'agit de remplacer les nombreuses lignes de code pour configurer l'application
			par un simple appel à une fonction.

			les fonctions créés sont les suivantes :

            - superimpose_otb(cloud_mask_img, nir_band_img, output_file, interpolator='nn', out_pixel_type=otbApplication.ImagePixelType_int16 , ram=4000)

            - bandmath_otb(il=[], il_object=[] , output_file='temp1.tif', exp='', ram=4000)

            - managenodata_otb(input_image,action, output_image, out_pixel_type=otbApplication.ImagePixelType_int16,  mode='changevalue')

            - extract_ROI_otb(input_file, shape_file, output_file, out_pixel_type=otbApplication.ImagePixelType_int16, mode='fit', ram=1000)

            - radiometric_indices_otb(input_file, output_file , nir_band_nb=1, red_band_nb=1, radiometric_indices=['Vegetation:NDVI'])


            ces fonctions étant un simple enrobages des fonctions d'otb je ne les décrirais pas plus
            en fonction des besoins l'utilisation de classe à la place de fonction peut être envisagé.

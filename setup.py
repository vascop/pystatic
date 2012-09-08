from setuptools import setup
setup(
    name = "pystatic",
    packages = ["pystatic"],
    scripts = ["bin/pystatic"],
    include_package_data = True,
    package_data = {
        "pystatic":
        [
            "pystatic/project/conf/vars.yaml",
            "pystatic/project/templates/*.html",
            "pystatic/project/assets/*.html",
            "pystatic/project/assets/css/*.css",
            "pystatic/project/assets/js/*.js",
            "pystatic/project/assets/js/*.css",
            "pystatic/project/assets/img/*.png",
            "pystatic/project/assets/fonts/*.eot",
            "pystatic/project/assets/fonts/*.svg",
            "pystatic/project/assets/fonts/*.ttf",
            "pystatic/project/assets/fonts/*.woff",
        ]
    },
    version = "0.1.23",
    description = "Static Website Generator",
    author = "Vasco Pinho",
    author_email = "vascogpinho@gmail.com",
    url = "https://github.com/vascop/pystatic",
    download_url = "https://github.com/vascop/pystatic/zipball/master",
    keywords = ["generator", "static website", "html"],
    install_requires=[
        "Django >= 1.4.1",
        "pyinotify >= 0.8.9",
        "pyyaml"
    ],
    license='LICENSE',
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Operating System :: POSIX :: Linux",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Code Generators",
        ],
    long_description = open('README').read()
)
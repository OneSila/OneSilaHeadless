source venv/bin/activate
cd OneSila
coverage run ./manage.py test $1
coverage html

echo "Open the results in html (y/n)?"
read answer

if [ "$answer" != "${answer#[Yy]}" ] ;then # this grammar (the #[] operator) means that the variable $answer where any Y or y in 1st position will be dropped if they exist.
    open htmlcov/index.html
fi

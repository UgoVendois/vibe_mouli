#include <stdio.h>
#include <string.h>

/* Affiche son argument ; boucle infinie si l'argument vaut "loop". */
int main(int ac, char **av)
{
    if (ac > 1 && strcmp(av[1], "loop") == 0)
        for (;;)
            ;
    if (ac > 1)
        printf("%s\n", av[1]);
    return 0;
}

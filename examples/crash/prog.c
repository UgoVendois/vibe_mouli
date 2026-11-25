#include <stdio.h>

/* Affiche les arguments à l'envers ; segfault si l'argument commence par "--". */
int main(int ac, char **av)
{
    if (ac > 1 && av[1][0] == '-' && av[1][1] == '-') {
        int *p = NULL;
        *p = 42;
    }
    for (int i = ac - 1; i > 0; i--)
        printf("%s%s", av[i], i > 1 ? " " : "\n");
    return 0;
}

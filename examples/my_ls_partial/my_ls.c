#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int cmp(const void *a, const void *b)
{
    return strcmp(*(char *const *)a, *(char *const *)b);
}

/* Version partielle : pas d'option, les fichiers cachés sont ignorés. */
int main(int ac, char **av)
{
    const char *path = ac > 1 ? av[1] : ".";
    DIR *d = opendir(path);
    char **names = NULL;
    size_t n = 0;
    size_t cap = 0;
    struct dirent *e;

    if (!d) {
        fprintf(stderr, "my_ls: cannot access '%s'\n", path);
        return 84;
    }
    while ((e = readdir(d)) != NULL) {
        if (e->d_name[0] == '.')
            continue;
        if (n == cap) {
            cap = cap ? cap * 2 : 16;
            names = realloc(names, cap * sizeof(char *));
        }
        names[n++] = strdup(e->d_name);
    }
    closedir(d);
    qsort(names, n, sizeof(char *), cmp);
    for (size_t i = 0; i < n; i++) {
        printf("%s\n", names[i]);
        free(names[i]);
    }
    free(names);
    return 0;
}

NAME = relink
CC = gcc

all: $(NAME)

$(NAME): FORCE
	$(CC) -o $(NAME) main.c

FORCE:

clean:
	rm -f *.o

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re FORCE

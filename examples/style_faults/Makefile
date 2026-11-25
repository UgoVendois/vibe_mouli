NAME = style_faults
CC = gcc

all: $(NAME)

$(NAME): main.c
	$(CC) -Wall -Wextra -o $(NAME) main.c

clean:
	rm -f *.o

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re

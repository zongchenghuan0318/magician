import pygame
from game.activity_page import ActivityPage

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('活动')
    activity_page = ActivityPage(screen)
    activity_page.open()
    running = True
    while running and activity_page.is_open:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            activity_page.handle_event(event)
        screen.fill((245, 245, 245))
        activity_page.draw()
        pygame.display.flip()
    pygame.quit()

if __name__ == '__main__':
    main() 
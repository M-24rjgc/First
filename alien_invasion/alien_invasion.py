import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """管理游戏资源和行为的类"""

    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()
       
        # 全屏运行
        # self.screen = pygame.display.set_mode.((0, 0), pygame.FULLSCREEN)
        # self.settings.screen_width = self.screen.get_rect().width
        # self.settings.screen_height = self.screen.get_rect().height

        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")
        self.bg_color = (230, 230, 230)

        # 创建一个用于存储游戏统计信息的实例, 并创建记分牌
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()
        # 游戏启动后处于活动状态
        self.game_active = False

        # 创建Play按钮
        self.play_button = Button(self, "Play")

    def _create_fleet(self):
        """创建一个外星舰队"""
        # 创建一个外星人,再不断添加，直到没有空间添加外星人为止
        # 外星人的间距为外星人的宽度和外星人的高度
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        
        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._creat_alien(current_x, current_y)
                current_x += 2 * alien_width

                # 创建完一行外星人后，将current_x重置为alien_width，current_y增加一个外星人的高度
            current_x = alien_width
            current_y += 2 * alien_height
            

        self.aliens.add(alien)

    def _creat_alien(self, x_position, y_position):
        """"创建一个外星人并将其放在当前行中"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _check_fleet_edges(self):
        """在有外星人到达屏幕边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edge():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整群外星人下移，并改变它们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1



    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()
            if self.game_active:

                self.ship.update()
                self.bullets.update()
                self._update_bullets()
                # print(len(self.bullets)) # 查看子弹数量
                self._update_aliens()
            self._update_screen()
            self.clock.tick(60)  # 每秒刷新60次

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """在玩家单击Play按钮时开始新游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            # 还原游戏设置
            self.settings.initialize_dynamic_settings()
            # 重置游戏统计信息
            self.stats.reset_stats()
            self.game_active = True

            # 清空外星人列表和子弹列表
            self.aliens.empty()
            self.bullets.empty()

            # 创建一群新的外星人并让飞船居中
            self._create_fleet()
            self.ship.center_ship()

            # 
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # 隐藏光标
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """响应按键"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """响应松开"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _update_bullets(self):
        """更新子弹的位置，并删除已消失的子弹"""
        self.bullets.update() # 更新子弹的位置 
        
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """检查是否有子弹击中了外星人，如果是，就删除相应的子弹和外星人"""
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
        # 删除现有的所有子弹，并创建一个新的外星舰队
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()    
        
        # 提高等级
            self.stats.level += 1
            self.sb.prep_level()

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)


        # 显示得分
        self.sb.show_score()

        # 如果游戏处于非活动状态，就显示Play按钮
        if not self.game_active:
            self.play_button.draw_button()

        pygame.display.flip()

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入编组中"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_aliens(self):
        """更新外星舰队中所有外星人的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        
        # 检查是否有外星人到达屏幕底端
        self._check_aliens_bottom()

    def _ship_hit(self):
        """响应飞船被外星人撞到"""
        if self.stats.ships_left > 0:
            # 将ships_left减1并更新记分牌
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # 清空子弹和外星人列表
            self.aliens.empty()
            self.bullets.empty()

            # 创建一群新的外星人，并将飞船放到屏幕底端中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停  
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """检查是否有外星人到达了屏幕底端"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites(): 
            if alien.rect.bottom >= screen_rect.bottom:
                # 像飞船被撞到一样处理
                self._ship_hit()
                break


if __name__ == '__main__':
    # 创建游戏对象并开始游戏
    ai = AlienInvasion()
    ai.run_game()
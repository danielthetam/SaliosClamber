import pygame
import sys
import os
import random
import math


class Ability:
    def __init__(self, name, description, pos, size, game, cost):
        self.name = name
        self.description = description
        self.cost = cost

        self.size = size
        self.og_pos = pos
        self.pos = pygame.Vector2(game.WINDOW_SIZE[0]/2, game.WINDOW_SIZE[1])
        self.game = game

        self.velocity = pygame.Vector2(0, 0)
        self.animation = None

        self.selected = False

        self.selected_color = (252, 136, 109)
        self.normal_color = (232, 116, 89)
        self.color = self.normal_color
        self.invalid_color = (255, 106, 79)

        self.invalid = False
        self.invalid_count = 0
        self.invalid_length = 8



    def render(self):
        if self.invalid:
            if self.invalid_count >= self.invalid_length:
                self.color = self.normal_color
                self.invalid_count = 0
                self.invalid = False
            else:
                self.invalid_count += 1

        elif not self.invalid:
            if self.selected and self.color != self.selected_color:
                self.color = self.selected_color
            elif not self.selected and self.color != self.normal_color:
                self.color = self.normal_color

        pygame.draw.rect(self.game.display, self.color, pygame.Rect(self.pos, self.size), 0, 16)
        font_size = self.game.card_font.size(self.name)
        font_position = (self.pos.x + (self.size[0]/2) - font_size[0]/2, self.pos.y + (self.size[1]/2) - font_size[1]/2)
        self.game.display.blit(self.game.card_font.render(self.name, True, (0, 0, 0)), font_position)


    def update(self):
        if self.animation is not None:
            if self.animation[4] < self.animation[5]:
                if self.animation[4] < self.animation[2]:
                    self.velocity += self.animation[1]
                elif self.animation[4] >= self.animation[3]:
                    self.velocity -= self.animation[1]
                else:
                    self.velocity = self.animation[0]

                self.animation[4] += 1

            elif self.animation[4] >= self.animation[5]:
                self.pos = pygame.Vector2(self.animation[6].x, self.animation[6].y)
                self.velocity = pygame.Vector2(0, 0)
                self.animation = None

        if (self.pos.x != self.og_pos.x or self.pos.y != self.og_pos.y) and self.animation is None:
            self.animation = self.animate(self.pos, self.og_pos, 30)


        if self.selected and self.animation is None:
            self.animation = self.animate(self.pos, pygame.Vector2(self.pos.x, self.og_pos.y - 30), 30)

        self.pos += self.velocity

    def invalidate(self):
        self.game.invalidate_sfx.play()
        self.color = self.invalid_color
        self.invalid = True


    def animate(self, starting_pos, ending_pos, time):
        a = ending_pos.x - starting_pos.x
        b = ending_pos.y - starting_pos.y
        full_speed = pygame.Vector2(a/(time * 0.8), b/(time * 0.8))

        acceleration =  full_speed/(time * 0.2)
        full_speed_time = (time * 0.2)
        deceleration_time = (time * 0.8)

        return [full_speed, acceleration, full_speed_time, deceleration_time, 0, time, ending_pos]

    def triggered(self):
        pass


class ResetCamera(Ability):
    def triggered(self):
        if not self.game.bomb_set:
            self.game.slow_down_sfx.play()
            self.game.camera_speed = self.game.initial_camera_speed


class Teleport(Ability):
    def triggered(self):
        self.game.teleport_sfx.play()
        top_platform = None
        for platform in self.game.platforms: 
            if platform[1].y >= 0:
                top_platform = platform[1]

        self.game.player_character.y = top_platform.y - self.game.player_character[3]
        self.game.player_character.x = top_platform.x + ((self.game.platform_size[0]/2) - (self.game.player_character[2]/2))

class UnlimitedJumps(Ability):
    def triggered(self):
        self.game.limit_jumps = False
        self.game.player_jumps = 2
        self.game.unlimited_jump_endtime = pygame.time.get_ticks() + self.game.unlimited_jump_length

class TripleJump(Ability):
    def triggered(self):
        self.game.triple_jump = True
        self.game.triple_jump_endtime = pygame.time.get_ticks() + self.game.triple_jump_length
        self.game.player_jumps = 3

class Bomb(Ability):
    def triggered(self):
        self.game.bomb_sfx.play()
        bomb_force = 100
        self.game.player_velocity.y = -bomb_force
        self.game.camera_speed = bomb_force
        self.game.player_jumps = 0
        self.game.bomb_set = True

        for i in range(3):
            rand_gradient = random.choice([(255, 124, 5), (255, 150, 55), (255, 166, 85)])
            particle_pos = pygame.Vector2(self.game.player_character.x + (self.game.player_size[0]/2), self.game.player_character.y + self.game.player_size[1])
            rand_size = random.randint(10, 15)
            self.game.particles.append(Particle(particle_pos, 10, rand_gradient, (rand_size, rand_size), (-10, 10), (10, 15), .01, self.game, True))


class TeleportNearestPlatform(Ability):
    def triggered(self):
        self.game.teleport_sfx.play()
        for platform in self.game.platforms:
            if platform[1].y < self.game.player_character.y:
                self.game.player_character.x = platform[1].x + (self.game.platform_size[0]/2) - (self.game.player_size[0]/2)
                self.game.player_character.y = platform[1].y - (self.game.player_size[1] - 5)
                break

class JumpBoost(Ability):
    def triggered(self):
        if not self.game.boost_jump:
            self.game.boost_sfx.play()
            self.game.player_jumps = 2
            self.game.boost_jump = True
            self.game.boost_jump_endtime = pygame.time.get_ticks() + self.game.boost_jump_length
        else:
            self.invalidate()


class SpeedBoost(Ability):
    def triggered(self):
        if not self.game.boost_speed:
            self.game.boost_sfx.play()
            self.game.player_speed *= 1.5
            self.game.boost_speed = True
            self.game.boost_speed_endtime = pygame.time.get_ticks() + self.game.boost_speed_length
        else:
            self.invalidate()


class ExtraLife(Ability):
    def triggered(self):
        self.game.extra_life += 1
        self.game.extra_life_endtime = pygame.time.get_ticks() + self.game.extra_life_length

class ZeroGravity(Ability):
    def triggered(self):
        self.game.zero_gravity_sfx.play()
        self.game.zero_gravity = True
        self.game.player_velocity.y = -5
        self.game.zero_gravity_endtime = pygame.time.get_ticks() + self.game.zero_gravity_length

class Jump(Ability):
    def triggered(self):
        self.game.power_jump_sfx.play()
        self.game.player_velocity.y = -self.game.player_jump_force * 1.5


class ExtraPoints(Ability):
    def triggered(self):
        self.game.extra_points = True
        self.game.extra_points_endtime = pygame.time.get_ticks() + self.game.extra_points_length

class Particle:
    def __init__(self, pos, particle_count, color, size, spread_range_x, spread_range_y, air_resistance, game, apply_time):
        self.game = game
        self.gravity_value = self.game.gravity
        self.air_resistance = air_resistance
        self.color = color
        self.apply_time = apply_time

        self.particles = []
        for i in range(particle_count):
            self.particles.append([pygame.Rect(pygame.Vector2(pos.x, pos.y), size), pygame.Vector2(random.randint(spread_range_x[0], spread_range_x[1]), random.randint(spread_range_y[0], spread_range_y[1]))])

    def render(self, display):
        for particle in self.particles:
            if self.apply_time:
                particle[0].y += particle[1].y * self.game.time
                particle[1].y += self.gravity_value * self.game.time
                particle[0].x += particle[1].x * self.game.time
                particle[1].x -= (math.copysign(1, particle[1].x) * self.air_resistance) * self.game.time
            else:
                particle[0].y += particle[1].y
                particle[1].y += self.gravity_value
                particle[0].x += particle[1].x
                particle[1].x -= math.copysign(1, particle[1].x) * self.air_resistance

            pygame.draw.rect(display, self.color, particle[0])

    def should_destroy(self, window_size_y):
        for particle in self.particles:
            if particle[0].y < window_size_y:
                return False
        return True

class Game:
    def __init__(self, WINDOW_SIZE, WINDOW_NAME, ICON_PATH):
        pygame.init()
        pygame.font.init()
        
        # Loading sfx
        pygame.mixer.init()
        self.jump_sfx = pygame.mixer.Sound(r"assets/jump.wav")
        self.invalidate_sfx = pygame.mixer.Sound(r"assets/invalidate.wav")
        self.boost_sfx = pygame.mixer.Sound(r"assets/boost.ogg")
        self.teleport_sfx = pygame.mixer.Sound(r"assets/teleport.wav")
        self.slow_down_sfx = pygame.mixer.Sound(r"assets/slow_down.wav")
        self.select_sfx = pygame.mixer.Sound(r"assets/select.wav")
        self.death_sfx = pygame.mixer.Sound(r"assets/death.wav")
        self.draw_card_sfx = pygame.mixer.Sound(r"assets/draw_card.ogg")
        self.rain_sfx = pygame.mixer.Sound(r"assets/rain.ogg")
        self.revived_sfx = pygame.mixer.Sound(r"assets/revived.ogg")
        self.bomb_sfx = pygame.mixer.Sound(r"assets/bomb.wav")
        self.zero_gravity_sfx = pygame.mixer.Sound(r"assets/zero_gravity.wav")
        self.open_hand_sfx = pygame.mixer.Sound(r"assets/open_hand.ogg")
        self.close_hand_sfx = pygame.mixer.Sound(r"assets/close_hand.ogg")
        self.rain_sfx = pygame.mixer.Sound(r"assets/rain.ogg")
        self.switch_card_sfx = pygame.mixer.Sound(r"assets/switch_card.ogg")
        self.power_jump_sfx = pygame.mixer.Sound(r"assets/powerJump.wav")
        self.hit_platform_sfx = pygame.mixer.Sound(r"assets/hit_platform.wav")
        
        self.boost_sfx.set_volume(.5)
        self.invalidate_sfx.set_volume(.2)
        self.jump_sfx.set_volume(.2)
        self.teleport_sfx.set_volume(.3)
        self.zero_gravity_sfx.set_volume(.5)
        self.power_jump_sfx.set_volume(.2)
        self.select_sfx.set_volume(.2)
        self.rain_sfx.set_volume(.3)
        self.rain_sfx.play(-1)

        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.WINDOW_SIZE = WINDOW_SIZE
        self.display = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption(WINDOW_NAME)
        icon = pygame.image.load(ICON_PATH)
        pygame.display.set_icon(icon)
        self.tDisplay = pygame.Surface(WINDOW_SIZE)
        self.reshuffle_cost = 5

        self.restart()

    def restart(self):
        self.tDisplay.set_alpha(100)
        self.tDisplay.fill((50, 50, 50))
        self.clock = pygame.time.Clock()

        self.player_size = (20, 40)
        self.player_character = pygame.Rect(pygame.Vector2(self.WINDOW_SIZE[0]/2 - (self.player_size[0]/2), self.WINDOW_SIZE[1]/2 - (self.player_size[1]/2)), self.player_size)
        self.player_velocity = pygame.Vector2(0, 0)
        self.player_jumps = 2
        self.player_jump_force = 10
        self.player_grounded = False
        self.player_left = False
        self.player_right = False
        self.player_speed = 5
        self.player_score = 0
        self.player_final_score = 0
        self.player_high_score = 0

        # Unlimited Jump Ability
        self.limit_jumps = True
        self.unlimited_jump_length = 10 * 1000
        self.unlimited_jump_endtime = 0

        # Triple Jump
        self.triple_jump = False
        self.triple_jump_length = 20 * 1000
        self.triple_jump_endtime = 0

        # Bomb
        self.bomb_set = False

        # Jump Boost
        self.boost_jump = False
        self.boost_jump_length = 10 * 1000
        self.boost_jump_endtime = 0

        # Speed Boost
        self.boost_speed = False
        self.boost_speed_length = 10 * 1000
        self.boost_speed_endtime = 0

        # Extra Life
        self.extra_life = 0
        self.revive = False
        self.extra_life_length = 60 * 1000
        self.extra_life_endtime = 0

        # Gravity
        self.zero_gravity = False
        self.zero_gravity_length = 15 * 1000
        self.zero_gravity_endtime = 0

        # Extra Points
        self.extra_points = False
        self.extra_points_length = 30 * 1000
        self.extra_points_endtime = 0

        self.platform_size = (150, 20)
        self.platforms = []
        self.platforms_rects = []
        self.platform_offset = 0.5 * self.player_size[0]
        self.platforms.append([False, pygame.Rect(pygame.Vector2(self.player_character.x - (self.platform_size[0]/2) + (self.player_character[2]/2), self.player_character.y + self.player_character[3] + 10), self.platform_size)])
        self.top_platform = self.platforms[0][1]
        self.edge_left = self.platform_size[0]
        self.edge_right = self.WINDOW_SIZE[0] - self.platform_size[0]
        self.generate_platforms(50)

        self.smoke_particles = []
        self.rain_particles = []
        self.rain_splash_particles = []
        self.rain_particle_size = (5, 50)
        self.particles = []

        self.initial_camera_speed = 2
        self.max_camera_speed = 4
        self.camera_speed = 0
        self.gravity = .4
        self.terminal_gravitational_velocity = 20

        self.game_over = False

        self.num_of_cards = 4
        self.draw_margin = 20

        self.abilities = []
        self.ability_deck = []
        self.selected_ability = 0
        self.ability_display = False
        ability_display_size = (0, self.WINDOW_SIZE[1]/9)
        ability_display_size = (ability_display_size[1] * 7, ability_display_size[1])
        ability_display_pos = ((self.WINDOW_SIZE[0]/2) - (ability_display_size[0]/2), self.WINDOW_SIZE[1] - (self.WINDOW_SIZE[1] * .2))
        self.ability_display_bar = pygame.Rect(ability_display_pos, ability_display_size)
        self.card_size = ((self.ability_display_bar[2] - (self.draw_margin * (self.num_of_cards + 1)))/self.num_of_cards, 0)
        self.card_size = (self.card_size[0], self.card_size[0] * 1.5)
        self.card_font_size = int(self.card_size[0]/16)
        self.card_font = pygame.font.Font("dogica.ttf", self.card_font_size)
        self.desc_font = pygame.font.Font("dogica.ttf", int(self.card_font_size * 1.3))
        ability_desc_pos = (ability_display_pos[0] + ability_display_size[0] + (0.05 * ability_display_size[0]), 0)
        self.ability_desc = pygame.Rect(ability_desc_pos, (self.WINDOW_SIZE[0] - ability_desc_pos[0], self.WINDOW_SIZE[1]))
        self.ability_name_position = (self.ability_desc.x + (0.1 * self.ability_desc.w), self.ability_desc.y + (0.1 * self.ability_desc.h))

        self.display_font = pygame.font.Font("Helmet-Regular.ttf", int(self.WINDOW_SIZE[0]/2))
        self.screen_font = pygame.font.Font("dogica.ttf", int(self.WINDOW_SIZE[0]/30))
        self.screen_font_small = pygame.font.Font("dogica.ttf", int(self.WINDOW_SIZE[0]/40))
        self.card_font = pygame.font.Font("dogica.ttf", int(self.card_size[0]/16))

        # Abilities
        pos = (0, 0)
        size = (0, 0)
        self.ability_deck.append(ResetCamera("Eyes of Lahan", "Slows the camera speed down to its initial speed", pos, size, self, 15))
        self.ability_deck.append(UnlimitedJumps("Sine Terminus", "Gives you unlimited jumps", pos, size, self, 25))
        self.ability_deck.append(Teleport("Summus's Throne", "Teleports the player to the top platform", pos, size, self, 20))
        self.ability_deck.append(TripleJump("Jump of Trinus", "Allows the player to triple jump", pos, size, self, 20))
        self.ability_deck.append(Bomb("Leap of Potentia", "Sends the player flying up", pos, size, self, 50))
        self.ability_deck.append(TeleportNearestPlatform("Ultimum's Reach", "Teleports the player to the nearest platform above them.", pos, size, self, 5))
        self.ability_deck.append(JumpBoost("Levo's Boost", "Boosts the player's jump force", pos, size, self, 15))
        self.ability_deck.append(SpeedBoost("Celerita's Boost", "Boosts the player's speed", pos, size, self, 15))
        self.ability_deck.append(ExtraLife("Life of Addo", "Lets the player respawn when they die", pos, size, self, 50))
        self.ability_deck.append(ZeroGravity("Nil Gravitas", "Puts the player in zero gravity space. ", pos, size, self, 25))
        self.ability_deck.append(Jump("Saltus", "Lets the player jump right now. ", pos, size, self, 5))
        self.ability_deck.append(ExtraPoints("Addo's Wealth", "Doubles the points the player gains", pos, size, self, 15))
        self.draw_from_deck(True, False)

        self.bg_color = (57, 58, 52)
        self.player_color = (208, 84, 50)
        self.platform_color = (13, 13, 13)
        self.score_color = (67, 68, 62)
        self.smoke_color = (89, 91, 90)
        self.rain_color = (47, 48, 42)

        self.time = 1

    def generate_platforms(self, platformCount):
        for i in range(platformCount):
            random_offset = random.randint(300, 350)
            position = None
            if (self.top_platform.x - random_offset) < self.edge_left:
                position = pygame.Vector2(self.top_platform.x + random_offset, self.top_platform.y - random.randint(200, 250))
            elif (self.top_platform.x + random_offset) > self.edge_right:
                position = pygame.Vector2(self.top_platform.x - random_offset, self.top_platform.y - random.randint(200, 250))
            else:
                position = pygame.Vector2(self.top_platform.x + (random_offset * random.choice([-1, 1])), self.top_platform.y - random.randint(200, 250))

            self.platforms.append([False, pygame.Rect(pygame.Vector2(position.x, position.y), self.platform_size)])
            self.top_platform = self.platforms[-1][1]

    def draw_from_deck(self, specific_index=True, play_sound=True):
        if play_sound:
            for i in range(2):
                self.draw_card_sfx.play()
        for i in range(self.num_of_cards - len(self.abilities)):
            random_ability = random.choice(self.ability_deck)
            self.ability_deck.remove(random_ability)
            size = ((self.ability_display_bar[2] - (self.draw_margin * (self.num_of_cards + 1)))/self.num_of_cards, 0)
            size = (size[0], size[0] * 1.5)
            pos = pygame.Vector2((self.ability_display_bar.x + (self.draw_margin * (len(self.abilities) + 1)) + (size[0] * len(self.abilities)), self.ability_display_bar.y - (size[1]/2)))
            random_ability.__init__(random_ability.name, random_ability.description, pos, size, self, random_ability.cost)
            if specific_index:
                self.abilities.insert(self.selected_ability, random_ability)
            else:
                self.abilities.append(random_ability)

    def revive_player(self):
        self.revived_sfx.play()
        self.player_velocity.y = 0
        self.player_character.y = -self.player_size[1]
        self.gravity = 0.05
        self.extra_life -= 1
        self.revive = True

    def end_game(self):
        if self.extra_life <= 0:
            self.death_sfx.play()
            self.bomb_set = False
            self.game_over = True
            self.ability_display = False
            self.time = 0

            with open("data.txt") as f:
                contents = f.read()
                self.player_high_score = int(contents)

            if self.player_high_score < self.player_final_score:
                with open("data.txt", "w") as f:
                    f.write(str(self.player_final_score))
                self.player_high_score = self.player_final_score
        else:
            self.revive_player()
        self.camera_speed = 0

    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == pygame.K_r:
                    if self.game_over:
                        self.select_sfx.play()
                        self.restart()
                    elif self.ability_display and self.player_score >= self.reshuffle_cost:
                        for ability in self.abilities:
                            ability.selected = False
                            self.ability_deck.append(ability)
                        self.abilities.clear()
                        self.player_score -= self.reshuffle_cost
                        self.draw_from_deck(False)
                    elif self.ability_display and self.player_score < self.reshuffle_cost:
                        self.invalidate_sfx.play()


                elif event.key == pygame.K_a:
                    if 0 <= self.player_velocity.y <= 1:
                        for i in range(2):
                            rand_size = random.randint(10, 25)
                            random_gradient = random.randint(80, 100)
                            self.smoke_particles.append([pygame.Rect(self.player_character.x - (20/2) + random.randint(-20, 20), self.player_character.y + self.player_size[1] - (self.player_size[1]/2) + random.randint(0, 20), rand_size, rand_size), random_gradient])
                    self.player_left = True

                elif event.key == pygame.K_d:
                    if 0 <= self.player_velocity.y <= 1:
                        for i in range(2):
                            rand_size = random.randint(10, 25)
                            random_gradient = random.randint(80, 100)
                            self.smoke_particles.append([pygame.Rect(self.player_character.x - (20/2) + random.randint(-20, 20), self.player_character.y + self.player_size[1] - (self.player_size[1]/2) + random.randint(0, 20), rand_size, rand_size), random_gradient])
                    self.player_right = True

                elif event.key == pygame.K_SPACE and self.player_jumps > 0:  # Jumping
                    if self.camera_speed == 0:
                        self.camera_speed = self.initial_camera_speed
                    if 0 <= self.player_velocity.y <= 1:
                        for i in range(5):
                            rand_size = random.randint(10, 25)
                            random_gradient = random.randint(80, 100)
                            self.smoke_particles.append([pygame.Rect(self.player_character.x - (20/2) + random.randint(-20, 20), self.player_character.y + self.player_size[1] - (self.player_size[1]/2) + random.randint(-20, 0), rand_size, rand_size), random_gradient])
                    self.player_grounded = False

                    self.player_velocity.y = -self.player_jump_force
                    if self.boost_jump:
                        self.player_velocity.y *= 1.5

                    if self.limit_jumps:
                        self.player_jumps -= 1
                    self.jump_sfx.play()

                elif event.key == pygame.K_TAB and not self.game_over:
                    self.ability_display = not self.ability_display
                    if self.ability_display:
                        self.rain_sfx.set_volume(0)
                        self.open_hand_sfx.play()
                        for key, ability in enumerate(self.abilities):
                            pos = pygame.Vector2((self.ability_display_bar.x + (self.draw_margin * (key + 1)) + (self.card_size[0] * key), self.ability_display_bar.y - (self.card_size[1]/2)))
                            ability.__init__(ability.name, ability.description, pos, self.card_size, self, ability.cost)
                            ability.animation = ability.animate(ability.pos, ability.og_pos, 30)
                        self.time = 0
                    else:
                        self.rain_sfx.set_volume(.3)
                        self.close_hand_sfx.play()
                        self.time = 1

                if event.key == pygame.K_q:
                    self.switch_card_sfx.play()
                    self.abilities[self.selected_ability].selected = False
                    if self.selected_ability - 1 >= 0:
                        self.selected_ability -= 1
                    else:
                        self.selected_ability = len(self.abilities) - 1

                elif event.key == pygame.K_e:
                    self.switch_card_sfx.play()
                    self.abilities[self.selected_ability].selected = False
                    if self.selected_ability + 1 < len(self.abilities):
                        self.selected_ability += 1
                    else:
                        self.selected_ability = 0

                elif event.key == pygame.K_RETURN:
                    if self.ability_display:
                        ability = self.abilities[self.selected_ability]
                        if self.player_score >= ability.cost:
                            self.rain_sfx.set_volume(.3)
                            self.draw_card_sfx.play()
                            self.abilities[self.selected_ability].triggered()
                            self.player_score -= ability.cost
                            self.particles.append(Particle(ability.pos, 10, (252, 136, 109), (10, 10), (-10, 10), (-10, -5), .06, self, False))
                            self.abilities.remove(ability)
                            ability.selected = False
                            self.ability_deck.append(ability)
                            self.draw_from_deck(True, False)

                            ability = self.abilities[self.selected_ability]
                            size = ((self.ability_display_bar[2] - (self.draw_margin * (self.num_of_cards + 1)))/self.num_of_cards, 0)
                            size = (size[0], size[0] * 1.5)
                            pos = pygame.Vector2((self.ability_display_bar.x + (self.draw_margin * (self.selected_ability + 1)) + (size[0] * self.selected_ability), self.ability_display_bar.y - (size[1]/2)))
                            ability.__init__(ability.name, ability.description, pos, size, self, ability.cost)
                            ability.animation = ability.animate(ability.pos, ability.og_pos, 30)

                            self.ability_display = False
                            self.time = 1
                        else:
                            ability.invalidate()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    self.player_left = False

                elif event.key == pygame.K_d:
                    self.player_right = False

            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        if self.player_left:
            self.player_velocity.x = -self.player_speed

        elif self.player_right:
            self.player_velocity.x = self.player_speed

        else:
            self.player_velocity.x = 0

        if not self.player_grounded and self.player_velocity.y < self.terminal_gravitational_velocity and not self.zero_gravity:
            self.player_velocity.y += self.gravity * self.time


        self.player_character.x += self.player_velocity.x * self.time
        self.player_character.y += self.player_velocity.y * self.time

        self.display.fill(self.bg_color)
        font_size = self.display_font.size(str(self.player_score))
        font_position = (self.WINDOW_SIZE[0]/2 - font_size[0]/2, self.WINDOW_SIZE[1]/2 - font_size[1]/2)
        self.display.blit(self.display_font.render(str(self.player_score), True, self.score_color), font_position)

        if len(self.rain_particles) < 100:
            for i in range(100 - len(self.rain_particles)):
                self.rain_particles.append([pygame.Rect(random.randint(0, self.WINDOW_SIZE[0]), random.randint(-2000, -50), self.rain_particle_size[0], self.rain_particle_size[1]), pygame.Vector2(random.uniform(-0.001, 0.001), random.randint(5, 10))])
        
        particles_to_remove = []
        splash_particles_to_remove = []
        for particle in self.rain_particles:
            particle[0].y += particle[1].y * self.time
            particle[0].y += self.camera_speed * self.time
            particle[0].x += particle[1].x * self.time
            if particle[0].y >= self.WINDOW_SIZE[1]:
                particles_to_remove.append(particle)        
                continue
            pygame.draw.rect(self.display, (self.rain_color), particle[0])

        for particle in self.rain_splash_particles:
            # rect, velocity
            particle[0].y += self.camera_speed * self.time
            particle[1].y += self.gravity * self.time
            particle[0].y += particle[1].y * self.time
            particle[0].x += particle[1].x * self.time
            particle[1].x -= math.copysign(1, particle[1].x) * 0.1
            if particle[0].y >= self.WINDOW_SIZE[1]:
                splash_particles_to_remove.append(particle)
                continue
            pygame.draw.rect(self.display, (self.rain_color), particle[0])

        for key, particle in enumerate(particles_to_remove):
            self.rain_particles.remove(particle)

        for key, particle in enumerate(splash_particles_to_remove):
            self.rain_splash_particles.remove(particle)

        for part in self.smoke_particles:
            random_decrease = random.uniform(.00000000000001, .00000000000002)
            if part[0][2] - random_decrease <= 0:
                self.smoke_particles.remove(part)

            part = part[0]
            part[1] -= .5
            part[2] -= random_decrease
            part[3] -= random_decrease

        for part in self.smoke_particles:
            pygame.draw.rect(self.display, (part[1], part[1], part[1]), part[0])


        # Platform
        platforms_to_remove = []
        if self.time < .5 and self.time != 0:
            self.player_character.y += self.camera_speed * .5
        else:
            self.player_character.y += self.camera_speed * self.time
        self.platforms_rects.clear()
        for platform in self.platforms:
            if self.time < .5 and self.time != 0:
                platform[1].y += self.camera_speed * .5
            else:
                platform[1].y += self.camera_speed * self.time

            if platform[1].y >= self.WINDOW_SIZE[1]:
                platforms_to_remove.append(platform)
                continue

            if len(self.platforms) <= 10:
                self.generate_platforms(50)

            pygame.draw.rect(self.display, self.platform_color, platform[1])
            self.platforms_rects.append(platform[1])
        
        rain_rects = []
        rain_rects_to_remove = []
        for particle in self.rain_particles:
            rain_rects.append(particle[0])

        for rect in self.platforms_rects:
            colliding_rain_rect = rect.collidelist(rain_rects)
            if colliding_rain_rect == -1:
                continue
            rand_size = random.randint(5, 8)
            for i in range(10):
                random_velocity = pygame.Vector2(random.randint(-5, 5), random.randint(-8, -5))
                position = pygame.Vector2(rain_rects[colliding_rain_rect].x, rain_rects[colliding_rain_rect].y)
                self.rain_splash_particles.append([pygame.Rect(position, (rand_size, rand_size)), random_velocity])
            rain_rects_to_remove.append(colliding_rain_rect)

        colliding_rain_rect = self.player_character.collidelist(rain_rects)
        if colliding_rain_rect != -1:
            rand_size = random.randint(5, 8)
            for i in range(10):
                random_velocity = pygame.Vector2(random.randint(-5, 5), random.randint(-8, -5))
                position = pygame.Vector2(rain_rects[colliding_rain_rect].x, rain_rects[colliding_rain_rect].y)
                self.rain_splash_particles.append([pygame.Rect(position, (rand_size, rand_size)), random_velocity])
            rain_rects_to_remove.append(colliding_rain_rect)

        for key, rect_index in enumerate(rain_rects_to_remove):
            del self.rain_particles[rect_index - key]


        # Prevents flickering of platforms when it is removed from the list
        for key, platform in enumerate(platforms_to_remove):
            self.platforms.remove(platform)
            if not self.bomb_set:
                if self.extra_points:
                    self.player_score += 2
                    self.player_final_score += 2
                else:
                    self.player_score += 1
                    self.player_final_score += 1
            else:
                if self.extra_points:
                    self.player_final_score += 2
                else:
                    self.player_final_score += 1

        platforms_to_remove = []
        platform_colliding = self.player_character.collidelistall(self.platforms_rects)
        if len(platform_colliding) != 0:
            for platform_rect in platform_colliding:
                platform_pos = pygame.Vector2(self.platforms_rects[platform_rect][0], self.platforms_rects[platform_rect][1])
                if self.bomb_set:
                    if self.player_velocity.y < 0:
                        platforms_to_remove.append(platform_rect)
                        self.particles.append(Particle(platform_pos, 30, self.platform_color, (10, 10), (-10, 10), (-10, -5), .06, self, True))
                        self.hit_platform_sfx.play()
                    else:
                        self.camera_speed = self.initial_camera_speed
                        self.bomb_set = False
                    continue


                elif platform_pos.x - self.player_size[0] + self.platform_offset < self.player_character.x < platform_pos.x + self.platform_size[0] - self.platform_offset:
                    if platform_pos.y > self.player_character.y and platform_pos.x - self.player_size[0] < self.player_character.x < platform_pos.x + self.platform_size[0]:
                        if not self.triple_jump:
                            self.player_jumps = 2
                        else:
                            self.player_jumps = 3


                        if self.revive:
                            self.revive = False
                            self.gravity = 0.4


                        self.player_grounded = True
                        self.player_velocity.y = 0
                        self.player_character.bottom = self.platforms_rects[platform_rect].top

                    elif platform_pos.y < self.player_character.y:
                        self.player_character.top = self.platforms_rects[platform_rect].bottom
                        if not self.zero_gravity:
                            self.player_velocity.y = .5
                else:
                    if platform_pos.x < self.player_character.x:
                        self.player_character.left = self.platforms_rects[platform_rect].right
                        self.player_grounded = False
                    elif platform_pos.x > self.player_character.x:
                        self.player_character.right = self.platforms_rects[platform_rect].left
                        self.player_grounded = False
        else:
            self.player_grounded = False


        for key, index in enumerate(platforms_to_remove):
            del self.platforms[index - key]
            if not self.bomb_set:
                if self.extra_points:
                    self.player_score += 2
                    self.player_final_score += 2
                else:
                    self.player_score += 1
                    self.player_final_score += 1

        if not self.camera_speed <= 0 and self.camera_speed < self.max_camera_speed:
            self.camera_speed += 0.0005 * self.time

        elif self.bomb_set and not self.camera_speed <= 0:
            self.camera_speed -= self.gravity
        elif self.camera_speed <= 0:
            self.camera_speed = 0

        pygame.draw.rect(self.display, self.player_color, self.player_character)  # Player

        if self.abilities[self.selected_ability].selected == False:
            self.abilities[self.selected_ability].selected = True

        if self.ability_display:
            self.display.blit(self.tDisplay, (0, 0))
            pygame.draw.rect(self.tDisplay, (0, 0, 0), self.ability_display_bar, 0, 16)

            # Ability description
            pygame.draw.rect(self.tDisplay, (0, 0, 0), self.ability_desc)
            ability = self.abilities[self.selected_ability]
            self.display.blit(self.desc_font.render(f"Title: {ability.name}", True, (255, 255, 255)), self.ability_name_position)
            desc_position = (self.ability_name_position[0], self.ability_name_position[1] + (0.1 * self.ability_desc.h))
            lines = []
            words = ""
            for word in ability.description.split():
                if desc_position[0] + self.desc_font.size(words + word)[0] > self.WINDOW_SIZE[0]:
                    lines.append(words)
                    words = word + " "
                    continue
                else:
                    words += (word + " ")
            if words != "":
                lines.append(words)

            last_desc_position = 0
            for key, line in enumerate(lines):
                line_height = self.desc_font.size(line)[1] + 10
                desc_position = (self.ability_name_position[0], self.ability_name_position[1] + (0.1 * self.ability_desc.h) + (key * line_height))
                self.display.blit(self.desc_font.render(line, True, (255, 255, 255)), desc_position)

                if key == (len(lines) - 1):
                    last_desc_position = desc_position

            self.display.blit(self.desc_font.render(f"Cost: {ability.cost}", True, (255, 255, 255)), (last_desc_position[0], last_desc_position[1] + (0.1 * self.ability_desc.h)))

            for ability in self.abilities:
                ability.update()
                ability.render()

        if not self.limit_jumps:
            if pygame.time.get_ticks() >= self.unlimited_jump_endtime:
                self.limit_jumps = True

        if self.triple_jump:
            if pygame.time.get_ticks() >= self.triple_jump_endtime:
                self.triple_jump = False

        if self.boost_jump:
            if pygame.time.get_ticks() >= self.boost_jump_endtime:
                self.boost_jump = False

        if self.boost_speed:
            if pygame.time.get_ticks() >= self.boost_speed_endtime:
                self.boost_speed = False
                self.player_speed /= 1.5

        if self.extra_life > 0:
            if pygame.time.get_ticks() >= self.extra_life_endtime:
                self.extra_life = 0

        if self.zero_gravity:
            if pygame.time.get_ticks() >= self.zero_gravity_endtime:
                self.camera_speed = self.initial_camera_speed
                self.zero_gravity = False
            else:
                self.camera_speed = abs(self.player_velocity.y) - .5

        if self.extra_points:
            if pygame.time.get_ticks() >= self.extra_points_endtime:
                self.extra_points = False

        if self.bomb_set and self.player_velocity.y > 0 and self.player_character.y >= self.WINDOW_SIZE[1] and not self.game_over:
            self.end_game()

        if self.player_character.y >= self.WINDOW_SIZE[1] and not self.bomb_set and not self.game_over: # Player Loses
            self.end_game()

        if self.player_character.y < -self.player_size[1]:
            if self.player_velocity.y <= 0:
                pygame.draw.rect(self.display, (255, 255, 255), pygame.Rect(self.player_character.x, -10, 10, 50), 0, 16)
            else:
                pygame.draw.rect(self.display, (255, 0, 0), pygame.Rect(self.player_character.x, -10, 10, 50), 0, 16)

        for particle in self.particles:
            particle.render(self.display)
            if particle.should_destroy(self.WINDOW_SIZE[1]):
                self.particles.remove(particle)


        if self.game_over:
            self.tDisplay = pygame.Surface(self.WINDOW_SIZE)
            self.tDisplay.set_alpha(100)
            self.tDisplay.fill((50, 50, 50))

            top_text = "PLATFORMS TRAVERSED:"
            bot_text = "Press 'R' to Restart"
            most_bot_text = f"HIGHEST PEAK: {self.player_high_score}"
            mid = (self.WINDOW_SIZE[0]/2 - (self.screen_font.size(str(self.player_score))[0]/2), self.WINDOW_SIZE[1]/2 - (self.screen_font.size(str(self.player_score))[0]/2))
            top = (self.WINDOW_SIZE[0]/2 - (self.screen_font.size(top_text)[0]/2), mid[1] - self.screen_font.size(top_text)[1] - (0.1 * self.WINDOW_SIZE[1]))
            bot = (self.WINDOW_SIZE[0]/2 - (self.screen_font.size(bot_text)[0]/2), mid[1] + self.screen_font.size(bot_text)[1] + (0.1 * self.WINDOW_SIZE[1]))
            most_bot = (self.WINDOW_SIZE[0]/2 - (self.screen_font_small.size(most_bot_text)[0]/2), bot[1] + self.screen_font.size(most_bot_text)[1] + (0.1 * self.WINDOW_SIZE[1]))

            back_size = (self.WINDOW_SIZE[0] * .8, self.WINDOW_SIZE[1] * .8)
            back = (self.WINDOW_SIZE[0]/2 - (back_size[0]/2), self.WINDOW_SIZE[1]/2 - (back_size[1]/2))
            pygame.draw.rect(self.tDisplay, (0, 0, 0), pygame.Rect(back, back_size), 0, 16)
            self.display.blit(self.tDisplay, (0, 0))
            self.display.blit(self.screen_font.render(str(self.player_final_score), True, (255, 255, 255)), mid)
            self.display.blit(self.screen_font.render(top_text, True, (255, 255, 255)), top)
            self.display.blit(self.screen_font.render(bot_text, True, (255, 255, 255)), bot)
            self.display.blit(self.screen_font_small.render(most_bot_text, True, (255, 255, 255)), most_bot)


        pygame.display.update()

        self.clock.tick(60)


    def run(self):
        self.process_input()
        self.update()

game = Game((1530, 800), "Salio's Clamber", r"salios_logo.png")

while True:
    game.run()

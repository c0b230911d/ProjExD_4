import math
import os
import random
import sys
import time
import pygame as pg



WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper": #もしhyperがオンなら
            self.image = pg.transform.laplacian(self.image) #見た目を透明に
            self.hyper_life -= 1 #残り時間減少
            if self.hyper_life < 0: #残り時間が0未満になったら
                self.state = "normal"#hyperをオフに
        screen.blit(self.image, self.rect)
    state = "normal" #初期状態 normal
    hyper_life = 0 #初期のこり時間 0


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"


        

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        引数 angle:ビームが回転する角度
        引数 angle:ビームが回転する角度
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        initial_angle = math.degrees(math.atan2(-self.vy,self.vx)) + angle
        initial_angle = math.degrees(math.atan2(-self.vy,self.vx)) + angle
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(initial_angle))
        self.vy = -math.sin(math.radians(initial_angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)
class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self,life:int):
        """
        重力場Surfaceを生成する
        引数 life：重力場の持続時間
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))  # 画面全体を覆う
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))  # (0, 0, 0)は黒色
        self.image.set_alpha(128)  # 透明度を設定
        self.rect = self.image.get_rect()
        self.life = life  # 重力場の持続フレーム数
    def update(self):
        """
        重力場の持続時間を管理し，0未満になったら削除
        """
        self.life -= 1
        if self.life < 0:
            self.kill()  # 重力場を削除

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        防御壁を生成する
        引数1 bird：防御壁を設置するこうかとん
        引数2 life：防御壁の寿命
        """
        super().__init__()
        self.life = life

        self.image = pg.Surface((20, bird.rect.height * 2), pg.SRCALPHA)
    
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height * 2))
        vx, vy = bird.dire
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        self.rect = self.image.get_rect()
        offset_x = vx * bird.rect.width
        offset_y = vy * bird.rect.height
        self.rect.centerx = bird.rect.centerx + offset_x
        self.rect.centery = bird.rect.centery + offset_y

    def update(self):

        self.life -= 1
        if self.life < 0:
            self.kill()
class SpeedBoost:
    def apply(bird, key_lst):
        if key_lst[pg.K_LSHIFT]:
            bird.speed = 20
        else:
            bird.speed = 10


class multiBeam:
    """
    複数の方向へビームを発射するクラス
    """
    def __init__(self, bird:Bird, num:int):
        """
        multiBeamクラスの初期化
        引数 bird:ビームを発射する工科トン
        引数 num:発射するビームの数
        """
        self.beams = self.gen_beams(bird, num)

    def gen_beams(self, bird:Bird, num:int) ->list:
        """
        指定されたビーム数に対して違う角度のビームを出す
        """
        beams = []
        #角度を一緒の間隔で設定
        angles = range(-50, 51, 100//(num-1))
        for angle in angles:
            beams.append(Beam(bird, angle))
        return beams
    
class multiBeam:
    """
    複数の方向へビームを発射するクラス
    """
    def __init__(self, bird:Bird, num:int):
        """
        multiBeamクラスの初期化
        引数 bird:ビームを発射する工科トン
        引数 num:発射するビームの数
        """
        self.beams = self.gen_beams(bird, num)

    def gen_beams(self, bird:Bird, num:int) ->list:
        """
        指定されたビーム数に対して違う角度のビームを出す
        """
        beams = []
        #角度を一緒の間隔で設定
        angles = range(-50, 51, 100//(num-1))
        for angle in angles:
            beams.append(Beam(bird, angle))
        return beams
    
class EMP(pg.sprite.Sprite):
    def __init__(self, emys : pg.sprite.Group, bombs : pg.sprite.Group, screen : pg.Surface):
        """
        電磁パルスのクラス
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        self.rect = self.image.get_rect()
        pg.draw.rect(self.image, (255, 255, 0, 128), self.rect)
        self.time = 10
        for emy in emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)
        for bomb in bombs:
            bomb.speed /= 2
            bomb.state = "inactive"

    def update(self):
        """
        時間を減算し、タイムアウト後に削除する
        """
        self.time -= 0.5
        if self.time <= 0:
            self.kill()

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()  
    emps = pg.sprite.Group()  # EMPのグループ
    gravity_fields = pg.sprite.Group()  # 重力場のグループを追加

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_e:  # 'E'キーでEMP発動
                    if len(emps) == 0:  # EMPが未発動の場合のみ発動
                        if score.value >= 20:  # スコアが20以上の場合のみ発動可能
                            emps.add(EMP(emys, bombs,screen))
                            score.value -= 20  # スコアを20減少

                if key_lst[pg.K_TAB]:
                    beams.add(*multiBeam(bird,5).beams)
                else:
                    beams.add(Beam(bird))
                if key_lst[pg.K_TAB]:
                    beams.add(*multiBeam(bird,5).beams)
                else:
                    beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value >= 100: #発動条件：右Shiftキー押下，かつ，スコアが100より大
                bird.state = "hyper" #無敵状態に
                bird.hyper_life = 500 #ライフを500フレームに
                score.value -= 100 #スコアを100減らす
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))  # ビーム発射
                if event.key == pg.K_s:
                    if score.value >= 50 and not shields:
                        shields.add(Shield(bird, 400))  
                        score.value -= 50  

            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value >= 10:
                # スコアが200以上の場合、RETURNキーで重力場を生成
                gravity_fields.add(Gravity(40))  # 持続時間40フレームの重力場を生成
                score.value -= 10  # スコアを10点消費
        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回、敵機を出現させる
        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現sさせる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 50  # 10点アップ
            score.value += 100  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
          # 重力場と爆弾・敵機との衝突判定
        for gravity in gravity_fields:
            for bomb in pg.sprite.spritecollide(gravity, bombs, True):
                exps.add(Explosion(bomb, 50))
            for emy in pg.sprite.spritecollide(gravity, emys, True):
                exps.add(Explosion(emy, 100))

        conbomb = pg.sprite.spritecollide(bird, bombs, True) #conbombに接触した爆弾の情報を格納
        if len(conbomb) != 0: #conbombが長さ0以外なら
            if bird.state == "hyper": #無敵なら
                exps.add(Explosion(conbomb[0], 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
            else:
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state == "inactive":
                continue



            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        for shield in pg.sprite.groupcollide(shields, bombs, False, True).keys():
            exps.add(Explosion(shield, 30))  # 衝突時に爆発エフェクト

        # 各オブジェクトの更新と描画
        SpeedBoost.apply(bird, key_lst)

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        shields.update()  
        shields.draw(screen)  
        emps.update()
        emps.draw(screen)  # EMPを描画
        gravity_fields.update()  # 重力場を更新
        gravity_fields.draw(screen)  # 重力場を描画
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
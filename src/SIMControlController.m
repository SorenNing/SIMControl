#import "SIMControlController.h"
#import <QuartzCore/QuartzCore.h>

@interface SIMControlController ()
@property(nonatomic,strong) UIButton *compactButton;
@property(nonatomic,strong) UIView *panel;
@property(nonatomic,strong) UIImageView *headerIcon;
@property(nonatomic,strong) UILabel *heading;
@property(nonatomic,strong) UILabel *message;
@property(nonatomic,strong) UIView *headerLine;
@property(nonatomic,strong) UIView *rowLine;
@property(nonatomic,strong) NSArray<SIMControlRow *> *rows;
@property(nonatomic,strong) NSArray<SIMControlItem *> *items;
@property(nonatomic) BOOL expanded;
@property(nonatomic) BOOL busy;
@property(nonatomic) NSUInteger readGeneration;
- (void)updateExpandedAppearance;
- (void)reload;
- (void)chooseRow:(SIMControlRow *)row;
@end

@implementation SIMControlController
- (void)loadView {
    self.view=[[UIView alloc] initWithFrame:CGRectMake(0,0,64,64)];
    self.view.backgroundColor=UIColor.clearColor;
    self.compactButton=[UIButton buttonWithType:UIButtonTypeCustom];
    UIImage *glyph=[UIImage imageNamed:@"CCSIM" inBundle:[NSBundle bundleForClass:self.class] compatibleWithTraitCollection:nil];
    if (!glyph) glyph=[UIImage systemImageNamed:@"simcard.2" withConfiguration:[UIImageSymbolConfiguration configurationWithPointSize:27 weight:UIImageSymbolWeightRegular]];
    glyph=[glyph imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
    [self.compactButton setImage:glyph forState:UIControlStateNormal];
    self.compactButton.tintColor=UIColor.whiteColor;
    self.compactButton.accessibilityLabel=@"SIM卡切换";
    [self.compactButton addTarget:self action:@selector(openPanel) forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:self.compactButton];
    self.panel=[UIView new];
    self.panel.backgroundColor=UIColor.clearColor;
    [self.view addSubview:self.panel];
    self.headerIcon=[[UIImageView alloc] initWithImage:glyph];
    self.headerIcon.tintColor=UIColor.whiteColor;
    self.headerIcon.contentMode=UIViewContentModeScaleAspectFit;
    [self.panel addSubview:self.headerIcon];
    self.heading=[UILabel new];
    self.heading.text=@"SIM卡切换";
    self.heading.textColor=UIColor.whiteColor;
    self.heading.textAlignment=NSTextAlignmentCenter;
    self.heading.font=[UIFont systemFontOfSize:18 weight:UIFontWeightSemibold];
    [self.panel addSubview:self.heading];
    self.headerLine=[UIView new];
    self.headerLine.backgroundColor=[UIColor colorWithWhite:1 alpha:0.28];
    [self.panel addSubview:self.headerLine];
    self.rowLine=[UIView new];
    self.rowLine.backgroundColor=[UIColor colorWithWhite:1 alpha:0.10];
    [self.panel addSubview:self.rowLine];
    NSMutableArray *rows=[NSMutableArray array];
    for (NSInteger slot=1;slot<=2;slot++) {
        SIMControlRow *row=[[SIMControlRow alloc] initWithFrame:CGRectZero];
        row.tag=slot;
        [row addTarget:self action:@selector(chooseRow:) forControlEvents:UIControlEventTouchUpInside];
        [self.panel addSubview:row]; [rows addObject:row];
    }
    self.rows=rows;
    self.message=[UILabel new];
    self.message.font=[UIFont systemFontOfSize:14];
    self.message.textAlignment=NSTextAlignmentCenter;
    self.message.textColor=UIColor.whiteColor;
    self.message.numberOfLines=2;
    [self.panel addSubview:self.message];
    [self updateExpandedAppearance];
}
- (double)preferredExpandedContentHeight { return 236.0; }
- (double)preferredExpandedContentWidth { return 336.0; }
- (bool)providesOwnPlatter { return false; }
- (bool)shouldBeginTransitionToExpandedContentModule { return !self.busy; }
- (bool)shouldFinishTransitionToExpandedContentModule { return true; }
- (bool)canDismissPresentedContent { return true; }
- (void)viewDidLayoutSubviews {
    [super viewDidLayoutSubviews];
    CGFloat width=CGRectGetWidth(self.view.bounds),height=CGRectGetHeight(self.view.bounds);
    self.compactButton.frame=self.view.bounds;
    self.panel.frame=self.view.bounds;
    // Keep the icon's centre at y=36 when increasing the glyph from 28 to 32pt.
    self.headerIcon.frame=CGRectMake((width-32)*0.5,20,32,32);
    self.heading.frame=CGRectMake(16,62,MAX(0,width-32),27);
    CGFloat pixel=1.0/MAX(1.0,self.view.window.screen.scale ?: UIScreen.mainScreen.scale);
    self.headerLine.frame=CGRectMake(0,102,width,pixel);
    CGFloat rowHeight=MAX(0,(height-102)*0.5);
    for (NSUInteger i=0;i<self.rows.count;i++) self.rows[i].frame=CGRectMake(0,102+i*rowHeight,width,rowHeight);
    self.rowLine.frame=CGRectMake(16,102+rowHeight,MAX(0,width-32),pixel);
    self.message.frame=CGRectMake(16,110,MAX(0,width-32),MAX(0,height-120));
}
- (void)openPanel {
    if (self.busy || ![self.moduleContext respondsToSelector:@selector(requestExpandModule)]) return;
    [self.moduleContext requestExpandModule];
}
- (void)updateExpandedAppearance {
    self.compactButton.hidden=self.expanded;
    self.panel.hidden=!self.expanded;
    self.message.hidden=self.items.count==2;
    self.rowLine.hidden=self.items.count!=2;
    for (SIMControlRow *row in self.rows) {
        row.hidden=self.items.count!=2;
        for (SIMControlItem *item in self.items) if (item.slot==row.tag) [row updateWithItem:item busy:self.busy];
    }
    [self.view setNeedsLayout];
}
- (void)reload {
    NSUInteger generation=++self.readGeneration;
    self.message.text=@"正在读取 SIM 信息…";
    __weak typeof(self) weakSelf=self;
    [self.service readItems:^(NSArray<SIMControlItem *> *items,NSString *error) {
        typeof(self) self=weakSelf;
        if (!self || generation!=self.readGeneration) return;
        self.items=items;
        self.message.text=error ?: @"无法读取 SIM 信息";
        [self updateExpandedAppearance];
    }];
}
- (void)willTransitionToExpandedContentMode:(bool)expanded {
    self.expanded=expanded;
    [self updateExpandedAppearance];
    if (expanded) [self reload];
}
- (void)didTransitionToExpandedContentMode:(bool)expanded {
    self.expanded=expanded;
    [self updateExpandedAppearance];
}
- (void)controlCenterWillPresent { if (self.expanded) [self reload]; }
- (void)controlCenterDidDismiss {
    self.expanded=NO;
    self.readGeneration++;
    [self updateExpandedAppearance];
}
- (void)chooseRow:(SIMControlRow *)row {
    if (self.busy) return;
    SIMControlItem *selected=nil;
    for (SIMControlItem *item in self.items) if (item.slot==row.tag) selected=item;
    if (!selected.available) return;
    self.busy=YES;
    [self updateExpandedAppearance];
    __weak typeof(self) weakSelf=self;
    [self.service setItem:selected enabled:!selected.enabled completion:^(BOOL accepted,NSString *error) {
        typeof(self) self=weakSelf;
        if (!self) return;
        self.busy=NO;
        if (accepted) {
            if ([self.moduleContext respondsToSelector:@selector(dismissModule)]) [self.moduleContext dismissModule];
        } else {
            self.items=@[]; self.message.text=error ?: @"SIM 启停请求失败";
            [self updateExpandedAppearance];
        }
    }];
}
@end

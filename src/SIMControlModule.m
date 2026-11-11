#import "SIMControlController.h"

@interface SIMControlModule : NSObject <CCUIContentModule>
@property(nonatomic,strong) SIMControlController *controller;
@property(nonatomic,strong) CCUIContentModuleContext *contentModuleContext;
@end

@implementation SIMControlModule
- (UIViewController<CCUIContentModuleContentViewController> *)contentViewController {
    if (!self.controller) {
        self.controller=[SIMControlController new];
        self.controller.service=[SIMControlService new];
        self.controller.moduleContext=self.contentModuleContext;
    }
    return self.controller;
}
- (void)setContentModuleContext:(CCUIContentModuleContext *)context {
    _contentModuleContext=context;
    self.controller.moduleContext=context;
}
- (UIViewController *)backgroundViewController { return nil; }
@end

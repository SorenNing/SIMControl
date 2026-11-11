#import "SIMControlPrivate.h"
#import "SIMControlTypes.h"

@interface SIMControlController : UIViewController <CCUIContentModuleContentViewController>
@property(nonatomic,strong) CCUIContentModuleContext *moduleContext;
@property(nonatomic,strong) SIMControlService *service;
@end

#import <Foundation/Foundation.h>
#include <stdio.h>

static NSMutableDictionary* pluginMap;

@interface PluginObject : NSObject
{}
-(void)performCommand:(NSString*)command;
@end


static int loadBundle(NSString* bundlePath)
{
	if (pluginMap == nil) {
		pluginMap = [NSMutableDictionary dictionary];
		if (pluginMap == nil) {
			printf("** Cannot allocate plugin map\n");
			return -1;
		}
		[pluginMap retain];
	}

	NSBundle* bundle = [NSBundle bundleWithPath: bundlePath];
	if (bundle == NULL) {
		printf("** Cannot load bundle %s\n", [bundlePath UTF8String]);
		return -1;
	}

	Class pluginClass = [bundle principalClass];
	if (pluginClass == Nil) {
		printf("** No principle class in %s\n", [bundlePath UTF8String]);
		return -1;
	}

	PluginObject* pluginObject = [[pluginClass alloc] init];
	if (pluginObject == Nil) {
		printf("** No principle class in %s\n", [bundlePath UTF8String]);
		return -1;
	}

	[pluginMap setObject:pluginObject forKey:[bundlePath lastPathComponent]];
	return 0;
}


static int 
perform_commands(void)
{
static char gBuf[1024];
	char* ln;
	while ((ln = fgets(gBuf, 1024, stdin)) != NULL) {
		char* e = strchr(ln, '\n');
		if (e) { *e  = '\0'; }
		char* cmd = strchr(ln, ':');
		if (cmd == NULL) {
			if (strcmp(ln, "quit") == 0) {
				return (0);
			}
			printf("* UNKNOWN COMMAND: %s\n", ln);
		} else {
			*cmd++ = '\0';
			NSAutoreleasePool* pool = [[NSAutoreleasePool alloc] init];

			PluginObject* pluginObject = [pluginMap objectForKey:[NSString stringWithUTF8String:ln]];
			if (pluginObject == NULL) {
				printf("* NO OBJECT: %s\n", cmd);
				continue;
			}
			[pluginObject performCommand: [NSString stringWithUTF8String:cmd]];
			[pool release];
		}
	}
	return 0;
}


int main(int argc, char** argv)
{
	int i, r;
	NSAutoreleasePool* pool;

	pool = [[NSAutoreleasePool alloc] init];
	for (i = 1; i < argc; i++) {
		r = loadBundle([NSString stringWithUTF8String:argv[i]]);
		if (r != 0) {
			return 2;
		}
	}
	printf("+ loaded %d bundles\n", argc - 1);
	fflush(stdout);
	[pool release];
	return perform_commands();
}


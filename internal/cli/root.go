package cli

import (
	"errors"
	"fmt"
	"io"

	"github.com/spf13/cobra"
)

// Execute runs the bootstrap command with explicit output destinations.
func Execute(args []string, stdout, stderr io.Writer) error {
	if stdout == nil || stderr == nil {
		return errors.New("output writers must not be nil")
	}

	var helpErr error
	root := &cobra.Command{
		Use:           "altruforge",
		Short:         "Maintainer-governed AI contributions (bootstrap)",
		SilenceErrors: true,
		SilenceUsage:  true,
		Args:          cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			return cmd.Help()
		},
	}
	root.SetOut(stdout)
	root.SetErr(stderr)
	root.SetArgs(args)
	// Cobra's HelpFunc has no error return. Preserve its writer failure and
	// return it from Execute, including when Cobra handles the help flag.
	root.SetHelpFunc(func(cmd *cobra.Command, _ []string) {
		_, err := fmt.Fprint(cmd.OutOrStdout(), cmd.Short+"\n\n"+cmd.UsageString())
		helpErr = errors.Join(helpErr, err)
	})
	return errors.Join(root.Execute(), helpErr)
}
